import os
import requests

BASE_URLS = {
    "1999-2000": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/1999/DataFiles/",
    "2001-2002": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2001/DataFiles/",
    "2003-2004": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/",
    "2005-2006": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles/",
    "2007-2008": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2007/DataFiles/",
    "2009-2010": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2009/DataFiles/",
    "2011-2012": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/",
    "2013-2014": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2013/DataFiles/",
    "2015-2016": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2015/DataFiles/",
    "2017-2018": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/",
}

FILE_SUFFIXES = {
    "1999-2000": {
        "Demographics": "DEMO.xpt",
        "Dental": "OHXDENT.xpt",
        "CRP": "LAB11.xpt",
        "Mercury": "LAB06HM.xpt",
        "BMI": "BMX.xpt",
        "Smoking": "SMQ.xpt",
        "Diabetes": "DIQ.xpt",
    },
    "2001-2002": {
        "Demographics": "DEMO_B.xpt",
        "Dental": "OHXDEN_B.xpt",
        "CRP": "L11_B.xpt",
        "Mercury": "L06_2_B.xpt",
        "BMI": "BMX_B.xpt",
        "Smoking": "SMQ_B.xpt",
        "Diabetes": "DIQ_B.xpt",
    },
    "2003-2004": {
        "Demographics": "DEMO_C.xpt",
        "Dental": "OHXDEN_C.xpt",
        "CRP": "L11_C.xpt",
        "Mercury": "L06BMT_C.xpt",
        "BMI": "BMX_C.xpt",
        "Smoking": "SMQ_C.xpt",
        "Diabetes": "DIQ_C.xpt",
    },
    "2005-2006": {
        "Demographics": "DEMO_D.xpt",
        "Dental": "OHXDEN_D.xpt",
        "CRP": "CRP_D.xpt",
        "Mercury": "PbCd_D.xpt",
        "BMI": "BMX_D.xpt",
        "Smoking": "SMQ_D.xpt",
        "Diabetes": "DIQ_D.xpt",
    },
    "2007-2008": {
        "Demographics": "DEMO_E.xpt",
        "Dental": "OHXDEN_E.xpt",
        "CRP": "CRP_E.xpt",
        "Mercury": "PbCd_E.xpt",
        "BMI": "BMX_E.xpt",
        "Smoking": "SMQ_E.xpt",
        "Diabetes": "DIQ_E.xpt",
    },
    "2009-2010": {
        "Demographics": "DEMO_F.xpt",
        "Dental": "OHXDEN_F.xpt",
        "CRP": "CRP_F.xpt",
        "Mercury": "PbCd_F.xpt",
        "BMI": "BMX_F.xpt",
        "Smoking": "SMQ_F.xpt",
        "Diabetes": "DIQ_F.xpt",
    },
    "2011-2012": {
        "Demographics": "DEMO_G.xpt",
        "Dental": "OHXDEN_G.xpt",
        "CRP": "CRP_G.xpt",
        "Mercury": "PbCd_G.xpt",
        "BMI": "BMX_G.xpt",
        "Smoking": "SMQ_G.xpt",
        "Diabetes": "DIQ_G.xpt",
    },
    "2013-2014": {
        "Demographics": "DEMO_H.xpt",
        "Dental": "OHXDEN_H.xpt",
        "CRP": "CRP_H.xpt",
        "Mercury": "PBCD_H.xpt",
        "BMI": "BMX_H.xpt",
        "Smoking": "SMQ_H.xpt",
        "Diabetes": "DIQ_H.xpt",
    },
    "2015-2016": {
        "Demographics": "DEMO_I.xpt",
        "Dental": "OHXDEN_I.xpt",
        "CRP": "HSCRP_I.xpt",
        "Mercury": "PBCD_I.xpt",
        "BMI": "BMX_I.xpt",
        "Smoking": "SMQ_I.xpt",
        "Diabetes": "DIQ_I.xpt",
    },
    "2017-2018": {
        "Demographics": "DEMO_J.xpt",
        "Dental": "OHXDEN_J.xpt",
        "CRP": "HSCRP_J.xpt",
        "Mercury": "PBCD_J.xpt",
        "BMI": "BMX_J.xpt",
        "Smoking": "SMQ_J.xpt",
        "Diabetes": "DIQ_J.xpt",
    },
}

CBC_FILES = {
    "1999-2000": "L40_0.xpt",
    "2001-2002": "L25_B.xpt",
    "2003-2004": "L25_C.xpt",
    "2005-2006": "CBC_D.xpt",
    "2007-2008": "CBC_E.xpt",
    "2009-2010": "CBC_F.xpt",
    "2011-2012": "CBC_G.xpt",
    "2013-2014": "CBC_H.xpt",
    "2015-2016": "CBC_I.xpt",
    "2017-2018": "CBC_J.xpt",
}

# Add CBC file names into FILE_SUFFIXES
for cycle, cbc_file in CBC_FILES.items():
    if cycle in FILE_SUFFIXES:
        FILE_SUFFIXES[cycle]["CBC"] = cbc_file

def download_all(data_dir="nhanes_data"):
    """Download NHANES XPT files for all cycles."""
    os.makedirs(data_dir, exist_ok=True)
    for cycle in FILE_SUFFIXES:
        print(f"\nDownloading files for {cycle}")
        base_url = BASE_URLS[cycle]
        for label, filename in FILE_SUFFIXES[cycle].items():
            url = base_url + filename
            save_path = os.path.join(data_dir, filename)
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                    print(f"Downloaded {label}: {filename}")
                else:
                    print(f"Failed ({resp.status_code}): {filename}")
            except Exception as exc:
                print(f"Error downloading {filename}: {exc}")

if __name__ == "__main__":
    download_all()
