import pandas as pd


def df_open_po(open_po_file):
    data = pd.read_excel(open_po_file)
    ready_list = [
        "Purchasing Document",
        "Material",
        "Document Date",
        "Order Quantity",
    ]
    ready_data = data[ready_list]
    ready_data.reset_index(drop=True, inplace=True)
    return ready_data


def df_supplier_stock(stock_file):
    data = pd.read_excel(stock_file)
    ready_list = [
        "Calendar Day",
        "Customer Part #",
        "Qty on Hand",
    ]
    ready_data = data[ready_list]
    ready_data.reset_index(drop=True, inplace=True)
    return ready_data


def df_supplier_shipments(shipment_file):
    data = pd.read_excel(shipment_file)
    data.columns = data.iloc[0]
    data = data.iloc[1:, :]
    data = data.dropna(subset=["MAD Date"])
    ready_list = [
        "Customer Part #",
        "Customer PO #",
        "TDS PO #",
        "MAD Date",
        "SSD Qty",
        "ASN Qty",
    ]
    ready_data = data[ready_list]
    ready_data = ready_data.sort_values(by=["MAD Date"])
    ready_data.reset_index(drop=True, inplace=True)
    return ready_data


def df_open_projects(project_file):
    data = pd.read_excel(project_file)
    data.columns = data.iloc[4]
    data = data.iloc[5:]
    ready_list = [
        "Overall rate",
        "Customer",
        "Month",
        "SAP",
        "QTY",
        "Availability",
        "DDO",
        "DDO end date",
        "Comments / hints",
    ]
    ready_data = data[ready_list]
    ready_data.reset_index(drop=True, inplace=True)
    return ready_data


def df_incoming_shipments(shipment_file):
    data = pd.read_excel(shipment_file)
    ready_list = [
        "Customer Part #",
        "Ship out QTY",
        "FTS order",
    ]
    ready_data = data[ready_list]
    ready_data.reset_index(drop=True, inplace=True)
    return ready_data
