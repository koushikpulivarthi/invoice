GSTIN_RE = r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b"
PLATE_RE = r"\b[A-Z]{2}[ -]?\d{1,2}[ -]?[A-Z]{1,3}[ -]?\d{4}\b"
VIN_RE = r"\b[A-HJ-NPR-Z0-9]{17}\b"
IRN_RE = r"\b[a-f0-9]{64}\b"
PHONE_RE = r"(?:Phone|Ph|Tel|Mobile)\.?\s*[:\-]?\s*(\+?[\d(][\d()\s+\-]{6,}\d)"
EMAIL_RE = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
TAX_RATE_RE = r"(?i)tax\s*\(\s*([\d.]+)\s*%\s*\)"

COMMON_COLUMNS = [
    "File Name", "Category", "Invoice No", "Invoice Date", "Due Date", "Payment Terms",
    "Seller", "Seller Address", "Seller GSTIN", "Phone", "Email",
    "Buyer", "Buyer Company", "Buyer Address", "Buyer GSTIN",
    "Subtotal", "Tax Rate (%)", "Tax", "CGST", "SGST", "IGST", "Total",
    "Payment Method", "Bank", "Account No", "Routing No",
]

LINE_ITEM_COLUMNS = [
    "Invoice No", "Invoice Date", "Category", "File Name", "Line No",
    "Code / HSN", "Extra Info", "Description", "Qty", "Unit Price", "Amount", "Line Tax", "Line Total",
]

COMMON_FIELDS = {
    "Invoice No": {"labels": [r"invoice\s*(?:no|number|num|id|#)", r"^bill\s*(?:no|number)",
                              r"inv\s*no", r"^invoice"]},
    "Invoice Date": {"labels": [r"invoice\s*date", r"bill\s*date", r"date\s*of\s*(?:issue|invoice)",
                                r"^date"]},
    "Due Date": {"labels": [r"due\s*date", r"payment\s*due", r"due\s*on"]},
    "Payment Terms": {"labels": [r"payment\s*terms", r"terms"]},
    "Seller": {"labels": [r"seller", r"sold\s*by", r"billed\s*by", r"vendor", r"supplier"]},
    "Phone": {"regex": PHONE_RE, "group": 1},
    "Email": {"regex": EMAIL_RE},
    "Buyer": {"labels": [r"buyer", r"bill\s*to", r"billed\s*to", r"sold\s*to",
                         r"customer\s*name", r"^customer", r"client"]},
    "Buyer Company": {"labels": [r"company\s*name"]},
    "Buyer Address": {"labels": [r"address"]},
    "Subtotal": {"labels": [r"sub\s*total", r"taxable\s*(?:value|amount)"], "type": "number"},
    "Tax Rate (%)": {"regex": TAX_RATE_RE, "group": 1, "type": "number"},
    "Tax": {"labels": [r"nj\s*tax", r"sales\s*tax", r"tax"], "type": "number"},
    "CGST": {"labels": [r"cgst"], "type": "number"},
    "SGST": {"labels": [r"sgst", r"utgst"], "type": "number"},
    "IGST": {"labels": [r"igst"], "type": "number"},
    "Total": {"labels": [r"grand\s*total", r"total\s*amount", r"amount\s*payable",
                         r"net\s*payable", r"total\s*due", r"^total"], "type": "number"},
    "Payment Method": {"labels": [r"payment\s*method", r"payment\s*mode"]},
    "Bank": {"labels": [r"bank"]},
    "Account No": {"labels": [r"account\s*(?:no|number)", r"account"]},
    "Routing No": {"labels": [r"routing"]},
}

BLOCK_LABELS = {
    "Invoice No": r"invoice\s*(?:no|number|#)\.?",
    "Invoice Date": r"invoice\s*date",
    "Due Date": r"due\s*date",
    "Payment Terms": r"terms",
    "Subtotal": r"sub\s*total",
    "Total": r"total\s*due(?:\s*\([^)]*\))?|grand\s*total|total\s*amount|total",
}

GST_CATEGORY = "GST"
DEFAULT_CATEGORY = "Other"

CATEGORIES = {
    "Health": {
        "keywords": ["hospital", "clinic", "patient", "doctor", "consultation", "pharmacy",
                     "medicine", "diagnostic", "pathology", "ward", "surgery", "medical", "dental"],
        "fields": {
            "Patient Name":    {"labels": [r"patient\s*name", r"patient"]},
            "Patient ID/UHID": {"labels": [r"uhid", r"patient\s*(?:id|no\.?|number)", r"mrn"]},
            "Doctor Name":     {"labels": [r"doctor\s*name", r"doctor", r"consultant"]},
            "Department":      {"labels": [r"department", r"dept"]},
            "Admission Date":  {"labels": [r"admission\s*date", r"admitted\s*on", r"admit\s*date"]},
            "Discharge Date":  {"labels": [r"discharge\s*date", r"discharged\s*on"]},
            "Diagnosis":       {"labels": [r"diagnosis"]},
        },
    },
    "Automobiles": {
        "keywords": ["vehicle", "automobile", "motor", "garage", "workshop", "chassis", "engine",
                     "odometer", "tyre", "tire", "spare parts", "showroom", "two wheeler",
                     "four wheeler", "car", "bike"],
        "fields": {
            "Vehicle No":         {"regex": PLATE_RE},
            "Chassis No (VIN)":   {"regex": VIN_RE},
            "Engine No":          {"labels": [r"engine\s*(?:no|number)\.?"]},
            "Make & Model":       {"labels": [r"make\s*/?\s*model", r"model", r"make"]},
            "Odometer (km)":      {"labels": [r"odometer", r"odo\s*reading", r"km\s*reading"], "type": "number"},
            "Job / Service Type": {"labels": [r"service\s*type", r"job\s*type", r"job\s*card", r"service"]},
        },
    },
    "Webdesign": {
        "keywords": ["website", "web design", "web development", "landing page", "domain", "hosting",
                     "seo", "wordpress", "responsive", "web app", "ui/ux", "figma", "cms", "ssl",
                     "maintenance"],
        "fields": {
            "Project Name":        {"labels": [r"project\s*name", r"project", r"website\s*name"]},
            "Domain Name":         {"labels": [r"domain\s*(?:name)?", r"website\s*url", r"url"]},
            "Hosting Plan":        {"labels": [r"hosting\s*plan", r"hosting"]},
            "Package / Plan":      {"labels": [r"package", r"plan"]},
            "No. of Pages":        {"labels": [r"(?:no\.?\s*of\s*)?pages", r"number\s*of\s*pages"], "type": "number"},
            "Subscription Period": {"labels": [r"subscription\s*period", r"validity", r"billing\s*period"]},
        },
    },
    "Photography": {
        "keywords": ["photography", "photographer", "photo", "photoshoot", "photos", "camera",
                     "album", "videography", "videographer", "lens", "studio", "prints"],
        "fields": {
            "Event / Shoot Name": {"labels": [r"event\s*name", r"shoot\s*name", r"event", r"occasion"]},
            "Shoot Date":         {"labels": [r"shoot\s*date", r"date\s*of\s*shoot", r"event\s*date"]},
            "Location":           {"labels": [r"location", r"venue", r"place"]},
            "Shoot Type":         {"labels": [r"shoot\s*type", r"type\s*of\s*shoot", r"package"]},
            "No. of Photos":      {"labels": [r"no\.?\s*of\s*photos", r"number\s*of\s*photos", r"photos"], "type": "number"},
            "Hours Booked":       {"labels": [r"hours?", r"hrs"], "type": "number"},
        },
    },
    "Consulting": {
        "keywords": ["consulting", "consultancy", "consultant", "advisory", "retainer", "engagement",
                     "deliverable", "mentoring", "audit", "chartered accountant", "legal", "strategy",
                     "professional fees"],
        "fields": {
            "Engagement / Project": {"labels": [r"engagement", r"project\s*name", r"project", r"assignment"]},
            "Consultant Name":      {"labels": [r"consultant\s*name", r"consultant", r"advisor"]},
            "Service Period":       {"labels": [r"service\s*period", r"engagement\s*period", r"period"]},
            "Hours Billed":         {"labels": [r"man\s*hours?", r"hours?\s*billed", r"hours?"], "type": "number"},
            "Hourly / Day Rate":    {"labels": [r"hourly\s*rate", r"day\s*rate", r"rate"], "type": "number"},
            "Retainer Fee":         {"labels": [r"retainer(?:\s*fee)?"], "type": "number"},
        },
    },
    "Education": {
        "keywords": ["school", "college", "university", "course", "student", "tuition", "semester",
                     "academic", "institute", "lecture", "syllabus", "batch", "admission fee", "exam fee"],
        "fields": {
            "Student Name":         {"labels": [r"student\s*name", r"name\s*of\s*student", r"student"]},
            "Student ID / Roll No": {"labels": [r"roll\s*(?:no|number)\.?", r"student\s*id",
                                                r"enrol?ment\s*(?:no|number|id)\.?",
                                                r"reg(?:istration)?\s*no\.?"]},
            "Course / Program":     {"labels": [r"course\s*name", r"course", r"programme?", r"class"]},
            "Semester / Term":      {"labels": [r"semester", r"term"]},
            "Academic Year":        {"labels": [r"academic\s*year", r"session", r"year"]},
            "Fee Type":             {"labels": [r"fee\s*type", r"fee\s*head", r"fees?\s*for"]},
            "Institution":          {"labels": [r"institution", r"school", r"college", r"university"]},
        },
    },
    "Retail": {
        "keywords": ["retail", "supermarket", "store", "mart", "grocery", "cashier", "discount",
                     "sku", "barcode", "mrp", "outlet", "items"],
        "fields": {
            "Store Name":        {"labels": [r"store\s*name", r"store", r"outlet", r"shop\s*name"]},
            "Store Code":        {"labels": [r"store\s*code", r"outlet\s*code"]},
            "Total Items / Qty": {"labels": [r"total\s*(?:items|qty|quantity)", r"items", r"qty"], "type": "number"},
            "Discount":          {"labels": [r"discount", r"disc"], "type": "number"},
            "Payment Mode":      {"labels": [r"payment\s*mode", r"payment\s*method", r"mode\s*of\s*payment", r"paid\s*by"]},
            "Cashier":           {"labels": [r"cashier", r"sales\s*person"]},
        },
    },
    "Hotel": {
        "keywords": ["hotel", "resort", "inn", "guest", "room", "check-in", "check in", "check-out",
                     "check out", "nights", "tariff", "housekeeping", "minibar", "suite", "banquet"],
        "fields": {
            "Guest Name":       {"labels": [r"guest\s*name", r"name\s*of\s*guest", r"guest"]},
            "Room No":          {"labels": [r"room\s*(?:no|number)\.?", r"room"]},
            "Room Type":        {"labels": [r"room\s*type", r"category"]},
            "Check-in Date":    {"labels": [r"check[\s-]*in(?:\s*date)?", r"arrival"]},
            "Check-out Date":   {"labels": [r"check[\s-]*out(?:\s*date)?", r"departure"]},
            "No. of Nights":    {"labels": [r"(?:no\.?\s*of\s*)?nights?"], "type": "number"},
            "Tariff per Night": {"labels": [r"tariff", r"room\s*rate", r"rate\s*per\s*night"], "type": "number"},
        },
    },
    "Events": {
        "keywords": ["event", "exhibition", "conference", "seminar", "workshop", "concert", "festival",
                     "ticket", "tickets", "sponsorship", "stall", "exhibitor", "attendees", "wedding",
                     "decor", "catering", "banquet", "venue"],
        "fields": {
            "Event Name":            {"labels": [r"event\s*name", r"event", r"programme", r"program"]},
            "Event Date":            {"labels": [r"event\s*date", r"date\s*of\s*event"]},
            "Venue":                 {"labels": [r"venue", r"location", r"hall"]},
            "Ticket Type":           {"labels": [r"ticket\s*type", r"ticket", r"pass\s*type"]},
            "No. of Tickets/Guests": {"labels": [r"no\.?\s*of\s*(?:tickets|guests|attendees|pax)",
                                                 r"tickets?", r"guests?", r"pax"], "type": "number"},
            "Sponsorship / Stall":   {"labels": [r"sponsorship", r"stall(?:\s*no)?"]},
            "Organizer":             {"labels": [r"organi[sz]er", r"organi[sz]ed\s*by"]},
        },
    },
    "Logistics": {
        "keywords": ["logistics", "freight", "shipment", "consignment", "awb", "airway bill", "waybill",
                     "lorry", "truck", "transporter", "courier", "cargo", "consignor", "consignee",
                     "e-way", "eway", "container", "pickup", "delivery"],
        "fields": {
            "AWB / LR / Consignment No": {"labels": [r"awb(?:\s*no)?", r"airway\s*bill(?:\s*no)?",
                                                     r"lr\s*no\.?", r"consignment\s*(?:no|number|id)\.?",
                                                     r"docket\s*no\.?", r"tracking\s*(?:no|number|id)"]},
            "E-Way Bill No":       {"labels": [r"e-?way\s*bill(?:\s*no)?"]},
            "Origin":              {"labels": [r"origin", r"pickup\s*(?:location|from)", r"source"]},
            "Destination":         {"labels": [r"destination", r"delivery\s*location", r"drop\s*location"]},
            "Consignor":           {"labels": [r"consignor"]},
            "Consignee":           {"labels": [r"consignee"]},
            "Vehicle No":          {"regex": PLATE_RE},
            "Weight (kg)":         {"labels": [r"chargeable\s*weight", r"gross\s*weight", r"weight"], "type": "number"},
            "Distance (km)":       {"labels": [r"distance"], "type": "number"},
        },
    },
    "GST": {
        "generic": True,
        "keywords": ["gst", "gstin", "cgst", "sgst", "igst", "tax invoice", "hsn", "sac", "irn"],
        "fields": {
            "HSN/SAC Code":    {"labels": [r"hsn(?:\s*/\s*sac)?(?:\s*code)?", r"sac(?:\s*code)?"]},
            "Place of Supply": {"labels": [r"place\s*of\s*supply"]},
            "GST Rate":        {"labels": [r"gst\s*rate", r"tax\s*rate"], "type": "number"},
            "Reverse Charge":  {"labels": [r"reverse\s*charge"]},
            "IRN":             {"regex": IRN_RE},
        },
    },
}
