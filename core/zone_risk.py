def zone_risk(zone):

    risk_table = {
        "residential":10,
        "farmland":20,
        "forest":25,
        "industrial":35,
        "greenfield":15
    }

    return risk_table.get(zone,20)