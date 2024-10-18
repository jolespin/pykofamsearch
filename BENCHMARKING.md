## PyKofamSearch

### Full Database

#### 12 threads

```
$ pykofamsearch -i data/test.faa.gz  -o pykofamsearch.cpu12.tsv -b ~/Databases/KOFAM/database.pkl -p=12
Loading serialized KOFAM database
Performing HMMSearch: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 26162/26162 [02:22<00:00, 183.46it/s]

real	2m45.083s
user	25m7.288s
sys	0m18.592s
```

#### Single thread
```
$ pykofamsearch -i data/test.faa.gz  -o pykofamsearch.tsv -b ~/Databases/KOFAM/database.pkl -p=1
Loading serialized KOFAM database
Performing HMMSearch: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 26162/26162 [21:05<00:00, 20.68it/s]

real	21m34.051s
user	20m36.916s
sys	0m21.951s
```

### Enzymes Only
#### 12 threads
```
$ pykofamsearch -i data/test.faa.gz  -o pykofamsearch.enzymes.cpu12.tsv -b ~/Databases/KOFAM/database.enzymes.pkl -p=12
Loading serialized KOFAM database
Performing HMMSearch: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10544/10544 [00:50<00:00, 210.46it/s]

real	0m56.777s
user	9m22.172s
sys	0m5.767s
```

#### Single thread
```
$ pykofamsearch -i data/test.faa.gz  -o pykofamsearch.enzymes.tsv -b ~/Databases/KOFAM/database.enzymes.pkl -p=1
Loading serialized KOFAM database
Performing HMMSearch: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10544/10544 [07:33<00:00, 23.26it/s]

real	7m39.356s
user	7m32.192s
sys	0m6.974s
```
_________________________________________________________
## KofamScan

### Full Database

#### 12 threads

```
% time exec_annotation -o kofamscan_output.cpu_12.tsv -p ~/Databases/KOFAM/profiles -k ~/Databases/KOFAM/ko_list --cpu 12 -f detail-tsv ./test.faa

real	3m40.992s
user	20m8.443s
sys	5m54.489s
```

#### Single thread

```
% time exec_annotation -o kofamscan_output.tsv -p ~/Databases/KOFAM/profiles -k ~/Databases/KOFAM/ko_list --cpu 1 -f detail-tsv ./test.faa

real	21m53.938s
user	17m37.846s
sys	4m10.003s
```

