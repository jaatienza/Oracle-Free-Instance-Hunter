![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OCI SDK](https://img.shields.io/badge/OCI%20SDK-red.svg)

# Oracle-Instance-Hunter

## Project Overview
Oracle-Instance-Hunter is a professional Python tool for automated deployment and scaling of Oracle Cloud Infrastructure (OCI) ARM instances. It is designed to find and provision Always Free ARM instances, incrementally scaling them to the maximum available resources.

## Features
- **Automated Instance Provisioning**: Automatically launches a base ARM instance (1 OCPU / 6 GB RAM) if no active instance is found.
- **Incremental Scaling**: Continuously attempts to upgrade the instance resources until the target of 4 OCPUs and 24 GB RAM is reached.
- **Resilient Error Handling**: Gracefully handles common API errors, including `Out of capacity` and `401 NotAuthenticated` (due to time sync issues).
- **Robust Logging**: All operations are logged to both the console and a `hunter.log` file for easy monitoring and debugging.
- **Flexible Configuration**: Supports both relative and absolute paths for configuration files and SSH keys.

## Prerequisites
- Python 3.8+
- An Oracle Cloud Infrastructure account.

## Configuration

### 1. Install Dependencies
The only required library is the OCI Python SDK. Install it using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 2. OCI Configuration
Create a `config` file based on the provided `config.example`. This file must contain your tenancy OCID, user OCID, region, API key fingerprint, and the path to your private API key (`.pem` file).

**Example `config` file:**
```ini
[DEFAULT]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
key_file=/path/to/your/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..xxxxxx
region=eu-frankfurt-1
```

### 3. Script Configuration
Before running, you must edit `main.py` and set the following variables with your specific OCIDs:
- `SUBNET_ID`: The OCID of the subnet where the instance will be created.
- `IMAGE_ID`: The OCID of the ARM-based OS image to use (e.g., Oracle Linux).

## Usage
Run the script from your terminal. Provide the paths to your OCI config file and your SSH public key using the command-line arguments.

```bash
python main.py --config-path /path/to/your/config --private-key-path /path/to/your/id_rsa.pub
```

### Arguments
- `--config-path`: Path to the OCI config file. Defaults to `config` in the script directory.
- `--private-key-path`: Path to the SSH public key file (`.pub`) to be added to the instance. Defaults to `id_rsa.pub` in the script directory.

The script will start logging its activities to the console and to `hunter.log`. It will terminate automatically once the target instance shape is achieved.