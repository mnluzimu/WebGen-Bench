conda create -p env/webvoyager python=3.10 -y
conda activate env/webvoyager
cd webvoyager
pip install -r requirements.txt
pip install numpy

# rm proxies in "env\webvoyager\lib\site-packages\openai\_base_client.py", line 738