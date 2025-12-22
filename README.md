# Oracle-Instance-Hunter

## Project Overview
Oracle-Instance-Hunter is a professional Python tool for automated deployment and scaling of Oracle Cloud Infrastructure (OCI) ARM instances. It is designed to find and provision Always Free ARM instances, incrementally scaling them to the maximum available resources (4 OCPUs and 24 GB RAM).

The script runs continuously, monitoring for available capacity and automatically attempting to launch or upgrade an instance until the target shape is achieved. All operations are logged to both the console and a `hunter.log` file.

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
You need a standard OCI `config` file containing your tenancy OCID, user OCID, region, fingerprint, and the path to your private API key. This tool loads the configuration from a file specified by the `--config-path` argument.

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
Run the script from your terminal. Provide the paths to your OCI config file and your SSH public key using the command-line arguments. The script handles both relative and absolute paths.

```bash
python main.py --config-path /path/to/your/config --private-key-path /path/to/your/id_rsa.pub
```

### Arguments
- `--config-path`: Path to the OCI config file. Defaults to `config` in the script directory.
- `--private-key-path`: Path to the SSH public key file (`.pub`) to be added to the instance. Defaults to `id_rsa.pub` in the script directory.

The script will start logging its activities to the console and to `hunter.log`. It will terminate automatically once the target instance shape is achieved.
