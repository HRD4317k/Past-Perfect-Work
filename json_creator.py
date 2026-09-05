import json
import random

# Full category mapping from UI to model type
UI_TO_MODEL_PRODUCT_TYPE = {
    # Books
    "Novels": "novels", "Course Books": "course_books", "Books": "course_books", "Notes": "course_books",
    # Study
    "Whiteboard": "academic_accessories", "ED Drafter": "ed_drafter", "Chart Holder": "chart_holder",
    "Lab Coat": "lab_coat", "Calculator": "calculator", "Laptop Stand": "laptop_stand",
    "Study Lamp": "academic_accessories",
    # Electronics
    "Keyboard/Mouse": "mouse", "Writing Pad": "academic_accessories", "Kindle": "furniture",
    "HDD / SSD / GPU": "electrical_accessories", "Monitor": "electrical_appliances",
    "USB/LAN Devices": "electrical_accessories", "Trimmer": "electrical_appliances",
    "Controller/Consoles": "electrical_appliances", "Smartwatches": "watch",
    "Wifi Router": "electrical_accessories", "Extension Cord": "electrical_accessories",
    "Earbuds": "earbuds", "Speakers": "speaker", "Mouse": "mouse", "Power Bank": "power_bank",
    # Watches
    "Digital": "watch", "Analog": "watch", "Smartwatches": "watch",
    # Personal Accessories
    "Shoes": "furniture", "Musical Instruments": "speaker", "Belts": "lab_coat",
    "Bags": "watch", "Umbrella": "chart_holder",
    # Cycle
    "Gear": "cycle", "Gearless": "cycle",
    # Mattresses
    "Cotton": "mattress", "Foam": "mattress",
    # Fitness & Sports
    "Gym Gear": "office_chair", "Yoga Mat": "rack",
    "Skipping Rope": "mouse", "Rackets": "watch",
    # Hostel Essentials
    "Mosquito Nets/Rackets": "laptop_stand", "Curtains": "lab_coat", "Wooden Chair": "furniture",
    "Office Chair": "office_chair", "Shelves": "rack", "Decor": "mouse", "Buckets/Mugs": "novels",
    # Appliances and Kitchenware
    "Table Fan": "table_fan", "Cooler": "cooler", "Washing Machine": "washing_machine",
    "Induction": "electrical_appliances", "Kettle": "kettle", "Utensils/Cutlery": "academic_accessories",
    
}

# Map model types to broad condition categories
category_map = {
    "novels": "Books", "course_books": "Books",
    "academic_accessories": "Academic Accessories", "ed_drafter": "Academic Accessories",
    "chart_holder": "Academic Accessories", "lab_coat": "Personal Accessories",
    "calculator": "Academic Accessories", "laptop_stand": "Academic Accessories",
    "mouse": "Electronics", "books": "Books",
    "electrical_accessories": "Electronics", "electrical_appliances": "Electronics",
    "watch": "Watches", "earbuds": "Electronics", "speaker": "Electronics",
    "power_bank": "Electronics", "rack": "Personal Accessories",
    "cycle": "Cycles", "mattress": "Mattress",
    "office_chair": "Fitness and Sports", "furniture": "Hostel Essentials",
    "kettle": "Appliances & Kitchenware", "table_fan": "Appliances & Kitchenware",
    "cooler": "Appliances & Kitchenware"
}

# Detailed condition descriptions
condition_descriptions = {
    "Books": [
        "Brand new or barely opened, no markings or folds.",
        "Some notes or highlights, edges slightly worn.",
        "Heavily used with annotations, dog-eared pages, or cover wear."
    ],
    "Academic Accessories": [
        "Unused or like-new stationery, calculators, or lab tools.",
        "Functional with minor signs of use like scuffs or ink marks.",
        "Worn-out or heavily used, some tools may need minor fixing."
    ],
    "Electronics": [
        "New or barely used with original packaging, no scratches.",
        "Fully functional with light wear or minor cosmetic marks.",
        "Frequent usage evident, noticeable scratches or aging."
    ],
    "Hostel Essentials": [
        "Like new, barely used bedsheets, buckets, or lamps.",
        "Moderate signs of use, slightly faded or scratched.",
        "Visible wear, some parts discolored, aged, or dented."
    ],
    "Fitness and Sports": [
        "Unused or used once/twice, no wear or odor.",
        "Regularly used, minor sweat marks or scratches.",
        "Well-worn equipment or apparel, visible wear or loose stitching."
    ],
    "Cycles": [
        "New condition with no rust or tire wear.",
        "Ridden occasionally, some dust or minor scratches.",
        "Frequently used, rusted parts, faded paint, or worn tires."
    ],
    "Mattress": [
        "Clean and firm, used less than a month.",
        "Used moderately, slight softening or fabric creasing.",
        "Heavily used, sagging or visible stains."
    ],
    "Watches": [
        "No scratches, original strap and box intact.",
        "Minor wear on strap or dial, fully functional.",
        "Noticeable scratches or loose strap, older model."
    ],
    "Appliances & Kitchenware": [
        "Unopened or used once, spotless and working perfectly.",
        "Working with light discoloration or minor oil stains.",
        "Regularly used, stains, burnt marks, or chipped parts visible."
    ],
    "Personal Accessories": [
        "New condition bags, wallets, or belts, no creases or scuffs.",
        "Minor scratches or creases, but fully usable.",
        "Visible wear or loose threads, aged appearance."
    ],
    "Miscellaneous": [
        "Unused or like-new condition, no signs of wear.",
        "Lightly used with minor cosmetic wear.",
        "Heavily used, visible wear and tear."
    ]
}

# Logical original price ranges for each model type
original_price_ranges = {
    "novels": [150, 200, 250], "course_books": [400, 600, 800],
    "academic_accessories": [200, 300, 400], "ed_drafter": [400, 600, 750],
    "chart_holder": [150, 250, 300], "lab_coat": [300, 350, 400],
    "calculator": [1100, 1300, 1500], "laptop_stand": [500, 750, 1000],
    "mouse": [300, 500, 700], "books": [150, 250, 350],
    "electrical_accessories": [800, 1200, 1500], "electrical_appliances": [1500, 3000, 5000],
    "watch": [800, 1500, 2500], "earbuds": [1000, 1500, 2000],
    "speaker": [1000, 2000, 3000], "power_bank": [800, 1200, 1500],
    "rack": [400, 600, 800], "cycle": [3000, 6000, 9000],
    "mattress": [1000, 1500, 2000], "office_chair": [1500, 2500, 3500],
    "furniture": [1000, 2000, 3000], "kettle": [500,800,1300],
    "table_fan": [900, 1200, 1600], "cooler": [2000, 4000, 6000],"washing_machine":[10000,12000,15000]

}

def generate_survey_json(output_path="static/js/json.js"):
    
    question_id = 1
    subcat_keys = list(UI_TO_MODEL_PRODUCT_TYPE.keys())

    
    pages= [
    {
      "name": "page1",
      "elements": [
        {
          "type": "dropdown",
          "name": "college",
          "title": "Which college are you from?",
          "isRequired": True,
          "choices": [
            {
              "value": "IIT Kharagpur",
              "text": "IIT Kharagpur"
            },
            {
              "value": "Lucknow University",
              "text": "Lucknow University"
            },
            {
              "value": "IIT BHU",
              "text": "IIT BHU"
            },
            {
              "value": "BITS Pilani",
              "text": "BITS Pilani"
            },
            {
              "value": "BIT Mesra",
              "text": "BIT Mesra"
            },
            {
              "value": "BITS Goa",
              "text": "BITS Goa"
            },
            {
              "value": "BITS Hyderabad",
              "text": "BITS Hyderabad"
            }
          ],
          "showOtherItem": True
        }
      ]
    }
  ]


    
    
    
    while len(pages) < 6:
        subcat = random.choice(subcat_keys)
        model_type = UI_TO_MODEL_PRODUCT_TYPE[subcat]
        broad_cat = category_map.get(model_type, "Miscellaneous")

        condition_idx = random.randint(0, 2)
        age = random.choices([1, 2, 3, 4], weights=[1, 2, 3, 4])[0]
        orig_price = random.choice(original_price_ranges[model_type])
        desc = condition_descriptions[broad_cat][condition_idx]

        if subcat in ['Gear', 'Gearless']:
            subcat_label = subcat + ' cycle'
        elif subcat in ['Foam', 'Cotton']:
            subcat_label = subcat + ' mattress'
        else:
            subcat_label = subcat

        # Check for duplicates
        if any(page['elements'][0]['title'].endswith(f"{subcat}?") and
               str(orig_price) in page['elements'][1]['title'] for page in pages):
            continue

        price_q = {
            "type": "text",
            "name": f"{question_id},{broad_cat},{subcat},{condition_idx},{age},{orig_price}",           
            "isRequired": True,
            "title": f"How much would you pay for a {age}-year-old {subcat_label} (originally ₹{orig_price})?",
            "description": desc,
            "inputType": "number",
            "min": round(0.1 * orig_price, 0),
            "max": round(0.9 * orig_price, 0),
            "step": 10
        }

        pages.append({"name": f"page{len(pages)+1}", "elements": [price_q]})
        question_id += 1

    survey_json = {
        "title": "Past Perfect: Pricing Preference Survey",
        "description": "Help us tailor second-hand product prices to better fit your campus community. Your input ensures smarter deals and fairer listings for everyone.",
        "pages": pages,
        "showPrevButton": True,
        "showProgressBar": True,
        "headerView": "advanced"
    }

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("const json = ")
        json.dump(survey_json, f, indent=2)
        f.write(";")
