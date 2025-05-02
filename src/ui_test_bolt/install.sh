npm install -g pm2

pm2 delete all

# Kill broken ones
pm2 delete all

# Rebuild ecosystem config
python D:\research\bolt\APP-Bench\src\ui_test\start_service.py

# Start again
pm2 list
pm2 logs

python D:\research\bolt\APP-Bench\src\ui_test\start_service.py D:\research\bolt\APP-Bench\data\example\extracted