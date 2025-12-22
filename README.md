# Oracle-Instance-Hunter

Oracle-Instance-Hunter is a Python tool designed for automated Oracle Cloud Infrastructure (OCI) ARM instance deployment. It streamlines the process of provisioning ARM-based virtual machines within OCI environments.

## Usage

The tool can be run from the command line. You can specify the path to your OCI configuration file and your SSH public key file using the `--config-path` and `--private-key-path` arguments, respectively.

```bash
python main.py --config-path /path/to/your/oci_config --private-key-path /path/to/your/ssh_key.pub
```

**Note:** If `--config-path` and `--private-key-path` are not provided, the script will default to looking for `config` and `id_rsa.pub` in the same directory as `main.py`.