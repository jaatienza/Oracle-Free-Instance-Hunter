# Oracle-Instance-Hunter

## Project Overview
Oracle-Instance-Hunter is a Python tool designed for automated Oracle Cloud Infrastructure (OCI) ARM instance deployment and scaling. Its primary purpose is to streamline the process of provisioning and incrementally scaling ARM-based virtual machines within OCI environments, particularly targeting Always Free eligible instances to reach their maximum allocated resources (4 OCPUs, 24 GB RAM). The tool continuously monitors instances and attempts to upgrade them until the desired configuration is achieved.

## Prerequisites
To effectively use Oracle-Instance-Hunter, ensure you have the following in place:

*   **Python:** Python 3.8 or higher is required.
*   **OCI SDK for Python:** This SDK is essential for interacting with OCI APIs. Install it using pip:
    ```bash
    pip install -r requirements.txt
    ```
*   **OCI API Keys:** You need an OCI API key pair. This involves generating a private key (`.pem` file) and uploading its public key to your OCI user profile. Ensure you have the following details readily available:
    *   Fingerprint of your API key.
    *   Tenancy OCID.
    *   User OCID.
    *   Your OCI region (e.g., `eu-frankfurt-1`).
*   **OCI Configuration File:** A standard OCI configuration file (typically `~/.oci/config`) is required for authentication. This file will reference your private API key.
*   **SSH Public Key:** An SSH public key (`.pub` file) is necessary for injecting into the newly launched OCI instances, allowing secure SSH access.

## Configuration
Before running the tool, you need to configure both your OCI environment and the `main.py` script:

1.  **OCI Configuration File (`config`):**
    Ensure your OCI configuration file (defaulting to `config` in the script's directory, or specified via `--config-path`) is correctly set up. A typical entry looks like this:
    ```ini
    [DEFAULT]
    user=ocid1.user.oc1..xxxxxx
    fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
    key_file=/path/to/your/oci_api_key.pem # Ensure this path is correct
    tenancy=ocid1.tenancy.oc1..xxxxxx
    region=eu-frankfurt-1
    ```
    The `key_file` should point to your **private** API key.

2.  **`main.py` Variables:**
    Open `main.py` and update the following hardcoded variables in the `--- TWOJA KONFIGURACJA ---` section with your specific OCI resource OCIDs:
    *   `SUBNET_ID`: Replace `"SUBNETID"` with the OCID of your desired OCI subnet.
    *   `IMAGE_ID`: Replace `"IMAGEID"` with the OCID of the OS image you wish to use (e.g., Oracle Linux ARM image).

## Usage
1.  **Install Dependencies:**
    Make sure you have the OCI SDK installed:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Hunter:**
    Execute the `main.py` script from your terminal. You can specify the paths to your OCI configuration file and SSH public key:
    ```bash
    python main.py --config-path ./config --private-key-path ./id_rsa.pub
    ```
    *   `--config-path`: (Optional) Specifies the path to your OCI configuration file. Defaults to `config` in the script's directory.
    *   `--private-key-path`: (Optional) Specifies the path to your SSH public key file (e.g., `id_rsa.pub`). Defaults to `id_rsa.pub` in the script's directory.

    The script will continuously attempt to launch a base ARM instance (1 OCPU/6 GB RAM) if none is found. Once a base instance is active, it will then try to upgrade its resources incrementally until it reaches the target of 4 OCPUs and 24 GB RAM. The script will exit automatically once the target is achieved.