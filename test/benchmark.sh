# PyKofamSearch
# =============
# Full database
echo "PyKofamSearch | Full database"
time pykofamsearch.py -i data/test.faa.gz  -o pykofamsearch.cpu_12.tsv -b ~/Databases/KOFAM/database.pkl.gz -p=12
time pykofamsearch.py -i data/test.faa.gz  -o pykofamsearch.tsv -b ~/Databases/KOFAM/database.pkl.gz -p=1

# Enzymes only
echo "PyKofamSearch | Enzyme database"
time pykofamsearch.py -i data/test.faa.gz  -o pykofamsearch.cpu_12.enzymes.tsv -b ~/Databases/KOFAM/database.enzymes.pkl.gz -p=12
time pykofamsearch.py -i data/test.faa.gz  -o pykofamsearch.enzymes.tsv -b ~/Databases/KOFAM/database.enzymes.pkl.gz -p=1

# KofamScan
# Full database
time exec_annotation -o kofamscan_output.cpu_12.tsv -p ~/Databases/KOFAM/profiles -k ~/Databases/KOFAM/ko_list --cpu 12 -f detail-tsv data/test.faa
time exec_annotation -o kofamscan_output.tsv -p ~/Databases/KOFAM/profiles -k ~/Databases/KOFAM/ko_list --cpu 1 -f detail-tsv data/test.faa
