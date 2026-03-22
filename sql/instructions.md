## 1. Configurar Kaggle

- Descargar kaggle.json desde kaggle.com/account
- Copiar al directorio:
```bash
mkdir C:\Users\$env:USERNAME\.kaggle
copy .\kaggle.json C:\Users\$env:USERNAME\.kaggle\
```

## 2. Crear base de datos y schema
```bash
psql -U postgres -c "CREATE DATABASE insightsql;"
psql -U postgres -d insightsql -f schema.sql
```

## 3. Descargar dataset
```bash
bash download_olist.sh
```


```bash
## 4. Importar datos
pip install -r requirements.txt
python seed_olist.py
```


## 5. Verificar
```bash
psql -U postgres -d insightsql -f verify_seed.sql
``` 