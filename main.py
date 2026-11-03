import oci
import os
import sys
import time
import random
import argparse
import logging

# --- Configuration ---
# Te wartości są pobierane z Twojego środowiska/configu
SUBNET_ID = "ocid1.subnet.oc1.eu-frankfurt-1.xxxx"  
IMAGE_ID = "ocid1.image.oc1.eu-frankfurt-1.xxxx"   

# --- Target Always Free Shape ---
FINAL_OCPUS = 1.0
FINAL_MEMORY = 6.0
SHAPE = "VM.Standard.A1.Flex"

def setup_logging():
    log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler("hunter.log")
    file_handler.setFormatter(log_formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])

def format_ssh_key(raw_key):
    if "-----BEGIN" in raw_key:
        lines = raw_key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").split()
        base64_key = "".join(lines)
        return f"ssh-rsa {base64_key} generated-by-py"
    return raw_key.strip()

def try_upgrade(compute_client, instance):
    current_cpu = instance.shape_config.ocpus
    current_ram = instance.shape_config.memory_in_gbs
    next_cpu = min(current_cpu + 1.0, FINAL_OCPUS)
    next_ram = min(current_ram + 6.0, FINAL_MEMORY)

    logging.info(f"Attempting upgrade: {current_cpu} OCPU -> {next_cpu} OCPU...")
    update_details = oci.core.models.UpdateInstanceDetails(
        shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(ocpus=next_cpu, memory_in_gbs=next_ram)
    )
    try:
        compute_client.update_instance(instance.id, update_details)
        logging.info(f"SUCCESS! Resources increased to {next_cpu} OCPU / {next_ram} GB RAM.")
        return True
    except oci.exceptions.ServiceError as e:
        if e.status == 429:
            return "RETRY_LATER"
        if "Out of capacity" in e.message or e.status == 500:
            logging.warning(f"No capacity for upgrade in current AD.")
        return False

def launch_initial(compute_client, compartment_id, ad_name, ssh_key):
    logging.info(f"Checking capacity in AD: {ad_name}...")
    launch_details = oci.core.models.LaunchInstanceDetails(
        compartment_id=compartment_id,
        availability_domain=ad_name,
        shape=SHAPE,
        display_name="MyAlwaysFreeARM",
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(ocpus=1, memory_in_gbs=6),
        source_details=oci.core.models.InstanceSourceViaImageDetails(image_id=IMAGE_ID),
        create_vnic_details=oci.core.models.CreateVnicDetails(subnet_id=SUBNET_ID, assign_public_ip=True),
        metadata={"ssh_authorized_keys": format_ssh_key(ssh_key)}
    )
    try:
        compute_client.launch_instance(launch_details)
        logging.info(f"✨ SUCCESS! Launched base instance in {ad_name}!")
        return True
    except oci.exceptions.ServiceError as e:
        if e.status == 429:
            return "RETRY_LATER"
        if "Out of capacity" in e.message or e.status == 500:
            logging.warning(f"AD {ad_name.split('-')[-1]}: Out of capacity.")
        else:
            logging.error(f"API Error: {e.message}")
        return False

def main():
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", default="config")
    parser.add_argument("--private-key-path", default="id_rsa.pub")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config_path)
    ssh_key_path = os.path.abspath(args.private_key_path)

    if not os.path.exists(config_path) or not os.path.exists(ssh_key_path):
        logging.error("Missing config or SSH key file!")
        sys.exit(1)

    with open(ssh_key_path, 'r') as f:
        ssh_key = f.read()

    config = oci.config.from_file(config_path)
    compute_client = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)
    compartment_id = config["tenancy"]

    # Pobierz wszystkie 3 domeny dostępności (AD)
    try:
        ad_list = [ad.name for ad in identity_client.list_availability_domains(compartment_id).data]
        logging.info(f"Hunter active. Monitoring domains: {ad_list}")
    except Exception as e:
        logging.error(f"Failed to fetch ADs: {e}")
        sys.exit(1)

    while True:
        try:
            instances = compute_client.list_instances(compartment_id).data
            active = [i for i in instances if i.shape == SHAPE and i.lifecycle_state not in ("TERMINATED", "TERMINATING")]

            if not active:
                # Pętla po wszystkich AD w jednym cyklu
                for ad in ad_list:
                    result = launch_initial(compute_client, compartment_id, ad, ssh_key)
                    if result == "RETRY_LATER":
                        logging.warning("Rate limit hit (429). Backing off...")
                        break 
                    if result is True:
                        break
                    time.sleep(2) # Mała przerwa między AD
            else:
                inst = active[0]
                if inst.shape_config.ocpus < FINAL_OCPUS or inst.shape_config.memory_in_gbs < FINAL_MEMORY:
                    res = try_upgrade(compute_client, inst)
                    if res == "RETRY_LATER":
                        logging.warning("Rate limit hit (429) during upgrade.")
                else:
                    logging.info("Target reached! Ending hunt.")
                    break
        
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                time.sleep(60)
            else:
                logging.error(f"Service Error: {e.message}")
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")

        # Losowy czas oczekiwania między pełnymi cyklami (wszystkie AD)
        wait = random.randint(10, 30)
        logging.info(f"Waiting {wait}s for next full cycle...")
        time.sleep(wait)

if __name__ == "__main__":
    main()
