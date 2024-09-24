import pandas as pd
import os
import logging

# Set up logging
logging.basicConfig(
    filename='ca_check.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
    )

def isTrustedCA(ca: str):
    ca = ca.strip()
    try:
        # Use an absolute path or a path relative to the script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "AllCertificateRecordsReport.csv")
        
        certRecord = pd.read_csv(csv_path)
        
        # Log the column names to check what's available
        logging.info(f"CSV columns: {certRecord.columns.tolist()}")
        
        # Try to find the correct column name
        cert_name_column = next((col for col in certRecord.columns if "certificate name" == col.lower()), None)
        
        if cert_name_column is None:
            logging.error("Could not find a column for Certificate Name")
            return {"is_trusted_ca": False}
        
        wellKnownCA = set(certRecord[cert_name_column].dropna().tolist())
        
        logging.info(f"Checking CA: {ca}")
        logging.info("First 5 well-known CAs:")
        for i, known_ca in enumerate(list(wellKnownCA)[:5]):
            logging.info(f"  {known_ca}")
        
        if ca.strip() in wellKnownCA:
            logging.info(f"Result: {ca} is a trusted CA")
            return {"is_trusted_ca": True}
        else:
            logging.info(f"Result: {ca} is not a trusted CA")
            return {"is_trusted_ca": False}
    
    except Exception as e:
        logging.error(f"Error in isTrustedCA: {str(e)}")
        return {"is_trusted_ca": False}

if __name__ == "__main__":
    print(isTrustedCA("GlobalSign GCC R6 AlphaSSL CA 2023"))
