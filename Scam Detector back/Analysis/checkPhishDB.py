import pandas as pd
import os
import logging

def checkPhishDB(url):
    url = url.strip()
    logging.info(f"Checking URL: {url}")
    try:
        # Use an absolute path or a path relative to the script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "verified_online.csv")
        
        phishDB = pd.read_csv(csv_path)
        
        # Log the column names to check what's available
        logging.info(f"CSV columns: {phishDB.columns.tolist()}")
        
        # Try to find the correct column name
        url_column = next((col for col in phishDB.columns if "url" == col.lower()), None)
        logging.info(f"URL column: {url_column}")
        
        if url_column is None:
            logging.error("Could not find a column for URL")
            return {"in_phish_db": False}
        
        inPhishDB = url in set(phishDB[url_column].dropna().tolist())
        
        return {"in_phish_db": inPhishDB}
    
    except Exception as e:
        logging.error(f"Error in checkPhishDB: {str(e)}")
        return {"in_phish_db": False}
