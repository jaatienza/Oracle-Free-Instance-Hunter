import oci
import os
import sys
import time
import random
import argparse

# --- Configuration (Adjust as needed) ---
# Ensure these values are correct for your OCI environment
SUBNET_ID = "ocid1.subnet.oc1.iad.xxxx"  # Example: "ocid1.subnet.oc1.iad.xxxx"
IMAGE_ID = "ocid1.image.oc1.iad.xxxx"   # Example: "ocid1.image.oc1.iad.xxxx"

# --- Target Always Free Shape ---
FINAL_OCPUS = 4.0
FINAL_MEMORY = 24.0
SHAPE = "VM.Standard.A1.Flex"

def format_ssh_key(raw_key):
    """Formats the raw SSH public key content into the required format."""
    if "-----BEGIN" in raw_key:
        lines = raw_key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").split()
        base64_key = "".join(lines)
        return f"ssh-rsa {base64_key} generated-by-py"
    return raw_key.strip()

def try_upgrade(compute_client, instance):
    """Attempts to upgrade the instance by +1 OCPU and +6 GB RAM."""
    current_cpu = instance.shape_config.ocpus
    current_ram = instance.shape_config.memory_in_gbs

    next_cpu = min(current_cpu + 1.0, FINAL_OCPUS)
    next_ram = min(current_ram + 6.0, FINAL_MEMORY)

    print(f"[{time.strftime('%H:%M:%S')}] Attempting upgrade: {current_cpu} OCPU / {current_ram} GB -> {next_cpu} OCPU / {next_ram} GB...")

    update_details = oci.core.models.UpdateInstanceDetails(
        shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(
            ocpus=next_cpu,
            memory_in_gbs=next_ram
        )
    )

    try:
        compute_client.update_instance(instance.id, update_details)
        print(f"!!! SUCCESS !!! Resources increased to {next_cpu} OCPU / {next_ram} GB RAM.")
        return True
    except oci.exceptions.ServiceError as e:
        if "Out of capacity" in e.message or e.status == 500:
            print(f"[{time.strftime('%H:%M:%S')}] No capacity available for the next upgrade step.")
        else:
            print(f"API Error during upgrade: {e.message}")
        return False

def launch_initial(compute_client, compartment_id, ad_name, ssh_key):
    """Launches a base instance with 1 OCPU / 6 GB RAM."""
    print(f"[{time.strftime('%H:%M:%S')}] Attempting to launch a base instance (1 OCPU / 6 GB)...")
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
        print(f"\n[{time.strftime('%H:%M:%S')}] !!! SUCCESS !!! Launched base instance (1 OCPU / 6 GB RAM).")
        return True
    except oci.exceptions.ServiceError as e:
        if "Out of capacity" in e.message or e.status == 500:
            print(f"[{time.strftime('%H:%M:%S')}] No capacity available to launch a base instance. Waiting...")
        else:
            print(f"API Error during launch: {e.message}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Oracle-Instance-Hunter: Automated OCI ARM instance deployment and scaling.")
    parser.add_argument("--config-path", default="config", help="Path to the OCI config file (absolute or relative).")
    parser.add_argument("--ssh-key-path", default="id_rsa.pub", help="Path to the SSH public key file (absolute or relative).")
    args = parser.parse_args()

    # --- 3. File Validation ---
    if not os.path.exists(args.config_path):
        print(f"Error: OCI config file not found at '{args.config_path}'")
        sys.exit(1)
    if not os.path.exists(args.ssh_key_path):
        print(f"Error: SSH public key file not found at '{args.ssh_key_path}'")
        sys.exit(1)

    # --- 1. Path Handling ---
    # Load SSH key from the specified path
    with open(args.ssh_key_path, 'r') as f:
        ssh_key = f.read()

    # Load OCI config from the specified path
    config = oci.config.from_file(args.config_path)
    compute_client = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)

    compartment_id = config["tenancy"]
    ad_name = identity_client.list_availability_domains(compartment_id).data[0].name

    print(f"Oracle ARM Instance Hunter started in region: {config['region']}.")
    print(f"Target: {FINAL_OCPUS} OCPUs, {FINAL_MEMORY} GB RAM.")

    while True:
        try:
            # Check for existing instances
            instances = compute_client.list_instances(compartment_id).data
            active = [i for i in instances if i.shape == SHAPE and i.lifecycle_state not in ("TERMINATED", "TERMINATING")]

            if not active:
                # STEP 1: If no instance exists, launch a base one
                launch_initial(compute_client, compartment_id, ad_name, ssh_key)
            else:
                inst = active[0]
                # STEP 2: If the instance is smaller than the target, upgrade it
                if inst.shape_config.ocpus < FINAL_OCPUS or inst.shape_config.memory_in_gbs < FINAL_MEMORY:
                    try_upgrade(compute_client, inst)
                else:
                    # STEP 3: If the target is reached, exit
                    print("\n" + "="*50)
                    print("CONGRATULATIONS! Your instance has reached the target:")
                    print(f"{inst.shape_config.ocpus} OCPUs and {inst.shape_config.memory_in_gbs} GB RAM.")
                    print("Script is now terminating.")
                    print("="*50)
                    break
        
        # --- 2. Handle 401 Errors ---
        except oci.exceptions.ServiceError as e:
            if e.status == 401:
                print(f"[{time.strftime('%H:%M:%S')}] Authentication Error (401): NotAuthenticated.")
                print("This might be due to a system time mismatch. Please ensure your system clock is synchronized.")
                print("Waiting 120 seconds before retrying...")
                time.sleep(120)
            else:
                print(f"A service error occurred: {e.message}")
                print("Waiting a random interval before retrying...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Waiting a random interval before retrying...")

        # Wait a random interval before the next attempt
        time.sleep(random.randint(30, 60))

if __name__ == "__main__":
    main()