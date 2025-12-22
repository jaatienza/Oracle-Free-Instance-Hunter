import oci
import os
import time
import random
import argparse

# --- TWOJA KONFIGURACJA ---
# Upewnij się, że te dane są poprawne (skopiowane z poprzednich kroków)
SUBNET_ID = "SUBNETID" # Wklej CAŁY OCID
IMAGE_ID = "IMAGEID"
# SSH_PUB_FILE = "SSHPUBFILE" # This will be replaced by argparse

# Docelowe limity Always Free
FINAL_OCPUS = 4.0
FINAL_MEMORY = 24.0
SHAPE = "VM.Standard.A1.Flex"

def format_ssh_key(raw_key):
    if "-----BEGIN" in raw_key:
        lines = raw_key.replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").split()
        base64_key = "".join(lines)
        return f"ssh-rsa {base64_key} generated-by-py"
    return raw_key.strip()

def try_upgrade(compute_client, instance):
    """Próbuje powiększyć instancję o +1 CPU i +6 GB RAM"""
    current_cpu = instance.shape_config.ocpus
    current_ram = instance.shape_config.memory_in_gbs
    
    next_cpu = min(current_cpu + 1.0, FINAL_OCPUS)
    next_ram = min(current_ram + 6.0, FINAL_MEMORY)
    
    print(f"[{time.strftime('%H:%M:%S')}] Próba ulepszenia: {current_cpu}CPU/{current_ram}GB -> {next_cpu}CPU/{next_ram}GB...")
    
    update_details = oci.core.models.UpdateInstanceDetails(
        shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(
            ocpus=next_cpu,
            memory_in_gbs=next_ram
        )
    )
    
    try:
        compute_client.update_instance(instance.id, update_details)
        print(f"!!! SUKCES !!! Zasoby zwiększone do {next_cpu} OCPU / {next_ram} GB RAM.")
        return True
    except oci.exceptions.ServiceError as e:
        if "Out of capacity" in e.message or e.status == 500:
            print(f"[{time.strftime('%H:%M:%S')}] Brak wolnych zasobów na kolejny krok ulepszenia.")
        else:
            print(f"Błąd API podczas ulepszania: {e.message}")
        return False

def launch_initial(compute_client, compartment_id, ad_name, ssh_key):
    """Tworzy bazową instancję 1 OCPU / 6 GB RAM"""
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
        print(f"\n[{time.strftime('%H:%M:%S')}] !!! SUKCES !!! Utworzono bazę 1 OCPU / 6 GB RAM.")
        return True
    except oci.exceptions.ServiceError as e:
        if "Out of capacity" in e.message or e.status == 500:
            print(f"[{time.strftime('%H:%M:%S')}] Brak wolnych zasobów na start (1/6). Czekam...")
        else:
            print(f"Błąd API podczas tworzenia: {e.message}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Oracle-Instance-Hunter: Automated OCI ARM instance deployment and scaling.")
    parser.add_argument("--config-path", default="config", help="Path to the OCI config file.")
    parser.add_argument("--private-key-path", default="id_rsa.pub", help="Path to the SSH public key file.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Wczytywanie klucza SSH
    with open(os.path.join(script_dir, args.private_key_path), 'r') as f:
        ssh_key = f.read()

    # Konfiguracja OCI
    config = oci.config.from_file(os.path.join(script_dir, args.config_path))
    compute_client = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)
    
    compartment_id = config["tenancy"]
    ad_name = identity_client.list_availability_domains(compartment_id).data[0].name
    
    print(f"Skrypt Zarządcy ARM uruchomiony we Frankfurcie.")

    while True:
        try:
            # Sprawdź instancje
            instances = compute_client.list_instances(compartment_id).data
            active = [i for i in instances if i.shape == SHAPE and i.lifecycle_state not in ("TERMINATED", "TERMINATING")]

            if not active:
                # KROK 1: Jeśli nie ma nic, stwórz 1/6
                launch_initial(compute_client, compartment_id, ad_name, ssh_key)
            else:
                inst = active[0]
                # KROK 2: Jeśli jest mniejsza niż 4/24, ulepszaj
                if inst.shape_config.ocpus < FINAL_OCPUS or inst.shape_config.memory_in_gbs < FINAL_MEMORY:
                    try_upgrade(compute_client, inst)
                else:
                    # KROK 3: Jeśli osiągnięto cel, wyłącz skrypt
                    print("\n" + "="*50)
                    print("GRATULACJE! Twoja instancja osiągnęła 4 OCPU i 24 GB RAM.")
                    print("Skrypt kończy pracę.")
                    print("="*50)
                    break
        except Exception as e:
            print(f"Wystąpił nieoczekiwany błąd: {e}")

        # Odczekaj od 30 do 60 sekund przed kolejną próbą
        time.sleep(random.randint(30, 60))

if __name__ == "__main__":
    main()