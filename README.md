# Dapp-Hunt

* [Live Demo](http://54.153.4.11:5000)

---

## Getting Started

Follow these steps to clone, set up, and run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/Aananda-giri/dapp-hunt
cd Dapp-Hunt
```

### 2. (Optional) Set Up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies.

```bash
# Install virtualenv if not already installed
pip install virtualenv

# Create a virtual environment
python3 -m virtualenv venv

# Activate the virtual environment
# On Linux/MacOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

> If the above commands do not activate the environment, try one of the following:
> ```
> .\venv\Scripts\Activate
> source venv/Scripts/activate
> source venv/bin/activate
> ```

### 3. Install Requirements

Install the required dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and add the following environment variables:

```
ATOMA_BEARER=<your-bearer-token>
mongo_uri=<your-mongodb-uri>
```

### 5. Run the Application

Start the Sanic server by running:

```bash
python3 app.py
```

### 6. Access the Application

Open your browser and visit:  
[http://0.0.0.0:5000](http://0.0.0.0:5000)

---

* Alternatively, for running in background (ubuntu):


```
[Unit]
Description=Sanic App Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/atoma
ExecStart=/home/ubuntu/venv/bin/python3 /home/ubuntu/atoma/app.py --host=0.0.0.0 --port=8000 --workers=4
Environment="PATH=/home/ubuntu/venv/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:
```bash
sudo systemctl enable app
sudo systemctl start app
```

3. Basic commands to manage your app:
```bash
# Check status
sudo systemctl status app

# Restart app
sudo systemctl restart app

# View logs
sudo journalctl -u app
```

This will:
- Keep your app running even after SSH session ends
- Automatically restart it if it crashes or terminates
- Provide basic logging
- Start automatically when the server reboots

### Notes

- Ensure that your MongoDB server is running and accessible via the `mongo_uri` provided in `.env`.
- Replace `<your-bearer-token>` and `<your-mongodb-uri>` with your actual values.
- For any issues, feel free to raise a GitHub issue or contact the maintainer.

---

Happy coding!


