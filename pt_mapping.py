UI_TO_MODEL_PRODUCT_TYPE = {
    # Books
    "Novels": "novels",
    "Course Books": "course_books", 
    "Books": "course_books",
    "Notes": "course_books",

    # Study
    "Whiteboard": "academic_accessories",   
    "ED Drafter": "ed_drafter",
    "Chart Holder": "chart_holder",
    "Lab Coat": "lab_coat",
    "Calculator": "calculator",
    "Laptop Stand": "laptop_stand",
    "Study Lamp": "academic_accessories",  

    # Electronics
    "Keyboard/Mouse": "mouse",
    "Writing Pad": "academic_accessories",  
    "Kindle": "books",
    "HDD / SSD / GPU": "electrical_accessories",
    "Monitor": "electrical_appliances",
    "USB/LAN Devices": "electrical_accessories",
    "Trimmer": "electrical_appliances",
    "Controller/Consoles": "electrical_appliances",
    "Smartwatches": "watch",
    "Wifi Router": "electrical_accessories",
    "Extension Cord": "electrical_accessories",
    "Earbuds": "earbuds",
    "Speakers": "speaker",
    "Mouse": "mouse",
    "Power Bank": "power_bank",

    # Watches
    "Digital": "watch",
    "Analog": "watch",
    "Smartwatches": "watch",

    # Personal Accessories 
    "Shoes": "lab_coat",              # wearable, closest depreciation pattern
    "Musical Instruments": "speaker", # similar electronic category
    "Belts": "lab_coat",              # small wearable
    "Bags": "rack",                   # item storage
    "Umbrella": "rack",               # long, collapsible item like a stand

    # Cycle
    "Gear": "cycle",
    "Gearless": "cycle",

    # Mattresses
    "Cotton": "mattress",
    "Foam": "mattress",

    # Fitness & Sports
    "Gym Gear": "office_chair",       # bulky, personal utility equipment
    "Balls": "mouse",                 # small, often replaced item
    "Yoga Mat": "rack",               # stored flat like chart_holder/rack
    "Skipping Rope": "mouse",         # small, portable item
    "Rackets": "mouse",               # handheld tech-adjacent item

    # Hostel Essentials
    "WiFi Router": "electrical_accessories",
    "Mosquito Nets/Rackets": "furniture",
    "Curtains": "furniture",
    "Wooden Chair": "furniture",
    "Office Chair": "office_chair",
    "Shelves": "rack",
    "Decor": "furniture",
    "Buckets/Mugs": "kettle",         # plastic/metal container, matches use case

    # Appliances and Kitchenware
    "Table Fan": "table_fan",
    "Cooler": "cooler",
    "Washing Machine": "electrical_appliances",
    "Induction": "electrical_appliances",
    "Kettle": "kettle",
    "Utensils/Cutlery": "kettle",     # same material, similar depreciation

    # Coupons and Promo Codes
    "Coupons and Promo Codes": "novels"  # digital, consumable-like, low-value item
}

condition_descriptions = {
    "Books": {
        "0": "Brand new or barely opened, no markings or folds.",
        "1": "Some notes or highlights, edges slightly worn.",
        "2": "Heavily used with annotations, dog-eared pages, or cover wear."
    },
    "Academic Accessories": {
        "0": "Unused or like-new stationery, calculators, or lab tools.",
        "1": "Functional with minor signs of use like scuffs or ink marks.",
        "2": "Worn-out or heavily used, some tools may need minor fixing."
    },
    "Electronics": {
        "0": "New or barely used with original packaging, no scratches.",
        "1": "Fully functional with light wear or minor cosmetic marks.",
        "2": "Frequent usage evident, noticeable scratches or aging."
    },
    "Hostel Essentials": {
        "0": "Like new, barely used bedsheets, buckets, or lamps.",
        "1": "Moderate signs of use, slightly faded or scratched.",
        "2": "Visible wear, some parts discolored, aged, or dented."
    },
    "Fitness and Sports": {
        "0": "Unused or used once/twice, no wear or odor.",
        "1": "Regularly used, minor sweat marks or scratches.",
        "2": "Well-worn equipment or apparel, visible wear or loose stitching."
    },
    "Cycles": {
        "0": "New condition with no rust or tire wear.",
        "1": "Ridden occasionally, some dust or minor scratches.",
        "2": "Frequently used, rusted parts, faded paint, or worn tires."
    },
    "Mattress": {
        "0": "Clean and firm, used less than a month.",
        "1": "Used moderately, slight softening or fabric creasing.",
        "2": "Heavily used, sagging or visible stains."
    },
    "Watches": {
        "0": "No scratches, original strap and box intact.",
        "1": "Minor wear on strap or dial, fully functional.",
        "2": "Noticeable scratches or loose strap, older model."
    },
    "Appliances & Kitchenware": {
        "0": "Unopened or used once, spotless and working perfectly.",
        "1": "Working with light discoloration or minor oil stains.",
        "2": "Regularly used, stains, burnt marks, or chipped parts visible."
    },
    "Personal Accessories": {
        "0": "New condition bags, wallets, or belts, no creases or scuffs.",
        "1": "Minor scratches or creases, but fully usable.",
        "2": "Visible wear or loose threads, aged appearance."
    },
    "Miscellaneous": {
        "0": "Unused or like-new condition, no signs of wear.",
        "1": "Lightly used with minor cosmetic wear.",
        "2": "Heavily used, visible wear and tear."
    }
}

img_json = {
    "Novels":"https://cdn.pixabay.com/photo/2018/07/11/16/53/book-3531412_1280.jpg",
    "Textbooks": "https://cdn.pixabay.com/photo/2014/10/14/20/14/library-488678_1280.jpg",
    "Whiteboard": "https://img.freepik.com/premium-vector/empty-whiteboard-magnetic-marker-with-shadow_108964-20.jpg?semt=ais_items_boosted&w=740",
    "ED Drafter": "https://m.media-amazon.com/images/I/712AHEn5i3L._UF1000,1000_QL80_.jpg",
    "Chart Holder": "https://m.media-amazon.com/images/I/51ovmGBNQ-L._UY1100_.jpg",
    "Lab Coat": "https://rukminim2.flixcart.com/image/850/1000/kw104nk0/hospital-scrub/b/s/0/unisex-lab-coat-apron-cotton-white-colour-for-medical-students-original-imag8sgsgwkebmh7.jpeg?q=90&crop=false",
    "Calculator": "https://m.media-amazon.com/images/I/61IujYL0JTL._UF1000,1000_QL80_.jpg",
    "Laptop_Stand": "https://symplify.in/cdn/shop/products/Wooden-Laptop-Stand-Opt3-3.jpg?v=1658253933",
    "Study Lamp": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQMmTIE0-ElsEaagFQlP8tUCnZVjGlwvsBlhA&s",
    "Keyboard/Mouse": "https://cdn.pixabay.com/photo/2016/10/30/13/46/smart-watch-1783180_1280.jpg",
    "Writing Pad": "https://instamart-media-assets.swiggy.com/swiggy/image/upload/fl_lossy,f_auto,q_auto,h_600/f70796fe7fc3416caf21820e1ba990ac",
    "Kindle": "https://images-cdn.ubuy.co.in/659d9c11fd55da5c303ba0d7-amazon-kindle-paperwhite-signature.jpg",
    "HDD / SSD / GPU": "https://cdn.pixabay.com/photo/2016/04/08/12/15/the-gpu-1316015_1280.png",
    "Monitor": "https://m.media-amazon.com/images/I/71+qQN-3KvL.jpg",
    "USB/LAN Devices": "https://cdn.pixabay.com/photo/2017/08/07/17/16/flashdisk-2605880_1280.jpg",
    "Trimmer": "https://beardo.in/cdn/shop/files/Beardo_Apex_Trimmer_A__Banner_2160x2160_03.jpg?v=1713352481&width=1946",
    "Controller/Consoles": "https://cdn.pixabay.com/photo/2021/09/07/07/11/game-console-6603120_1280.jpg",
    "Smartwatches": "https://gourban.in/cdn/shop/files/Pulse.jpg?v=1749553994&width=2048",
    "Wifi Router": "https://m.media-amazon.com/images/I/51DUq04ZEeL.jpg",
    "Extension Cord": "https://rukminim3.flixcart.com/image/850/1000/xif0q/surge-protector/k/s/f/2-dual-power-3-power-socket-3-usb-socket-yes-pick-ur-needs-original-imagr3utkgh6g8vu.jpeg?q=90&crop=false",
    "Earbuds": "https://www.leafstudios.in/cdn/shop/files/1_6b54ff34-acdd-40e6-a08a-f2bfa33a1c7a_800x.png?v=1718706988",
    "Speakers": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9cYWSaBNIhOPF2gguIun1olGtIYrHAlOO7w&s",
    "Mouse": "https://www.portronics.com/cdn/shop/files/Image1_5067bdd1-4473-4933-a66d-edcb4d49409a.png?v=1720258592&width=1445",
    "Power Bank": "https://images.philips.com/is/image/philipsconsumer/506144bc684c46e3a62fb0ce00a6d411?$pnglarge$&wid=1250",
    "Digital": "https://cdn.pixabay.com/photo/2023/11/16/10/26/casio-8392121_1280.jpg",
    "Analog": "https://cdn.pixabay.com/photo/2016/11/21/13/58/analog-watch-1845547_1280.jpg",
    "Shoes": "https://hips.hearstapps.com/hmg-prod/images/mhl-opener-run-shoes-311-67edd9f20e75a.jpg",
    "Musical Instruments": "https://www.normans.co.uk/cdn/shop/articles/musical_instruments_mix_2.jpg?v=1663668970",
    "Belts": "https://assets.myntassets.com/w_412,q_60,dpr_2,fl_progressive/assets/images/26916370/2024/1/14/d339f00d-fd36-4915-8647-7aa73ea04fca1705220360903RoadsterPackOf2FormalLeatherBelts1.jpg",
    "Bags": "https://studiocreative.in/cdn/shop/articles/Designer_Women_s_Bags_2048x.progressive_08859b56-9b2f-434d-a26e-ba830d831430.jpg?v=1730618479",
    "Umbrella": "https://cdn.thewirecutter.com/wp-content/media/2025/05/BEST-UMBRELLAS-WIND-RAIN-0373.jpg?auto=webp&quality=75&width=1024",
    "Gear": "https://ik.imagekit.io/voltebyk/models/1657026315871__HD__UJhXITlE2q__Small_.jpeg?updatedAt=1681732851864",
    "Gearless": "https://cdn.pixabay.com/photo/2022/07/29/10/33/bicycle-7351563_1280.jpg",
    "Cotton": "https://images.meesho.com/images/products/441623057/jdika_512.webp",
    "Foam": "https://cdn.pixabay.com/photo/2023/07/27/05/53/furniture-8152543_1280.jpg",
    "Gym Gear": "https://www.littleblokefitness.com.au/cdn/shop/articles/8af93b67f739fc6cb0a3cde8c4301346_d31b4237-47a1-49d9-8ab8-b53682838a84.jpg?v=1738280011",
    "Balls": "https://5.imimg.com/data5/SELLER/Default/2022/3/EJ/OT/UC/86909424/white-cricket-ball-500x500.JPG",
    "Yoga Mat": "https://sppartos.com/cdn/shop/files/31VX-aIlgWL.jpg?v=1702469142",
    "Skipping Rope": "https://m.media-amazon.com/images/I/71l2-gWOnpL.jpg",
    "Rackets": "https://cdn.shopify.com/s/files/1/0020/9407/1890/files/2_480x480.jpg?v=1559302854",
    "Mosquito Nets": "https://m.media-amazon.com/images/I/71e0Vw9+pnL.jpg",
    "Curtains": "https://drapestory.in/cdn/shop/files/19C_f7e75463-3503-465a-b8de-2eabc2bc1ceb.jpg?v=1694692991",
    "Wooden Chair": "https://m.media-amazon.com/images/I/517lhHFdW6L._UF1000,1000_QL80_.jpg",
    "Office Chair": "https://m.media-amazon.com/images/I/51A5WZTAYyL._UF894,1000_QL80_.jpg",
    "Shelves": "https://www.odejia.in/cdn/shop/files/81hoDRLhj1L._AC_SL1500.jpg?v=1724580332",
    "Decor": "https://pchomedecor.com/cdn/shop/products/images_2Fca1956ff-88db-49b2-8dac-1d5cf1dd36ff.jpg?v=1699364568",
    "Buckets/Mugs": "https://5.imimg.com/data5/SELLER/Default/2022/5/DP/XC/ZD/5818228/plastic-bucket-mug-set.jpg",
    "Table Fan": "https://cdn.accentuate.io/607456985392/-1695035269432/how-to-clean-a-table-fan--ma-v1714477106410.png?800x800",
    "Cooler": "https://images-cdn.ubuy.co.in/6350fad1476ca1256b24c916-portable-evaporative-air-cooler-outdoor.jpg",
    "Washing Machine": "https://whirlpoolindia.vtexassets.com/arquivos/ids/164386/Xpert-care-Silver-lid-open-O3-6.5kg_1500x1500.jpg?v=638731267672600000",
    "Induction": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRnM3DMTMUGiQzt_K5_6JmuJMBpszz9Oyl8CQ&s",
    "Kettle": "https://www.wonderchef.com/cdn/shop/files/6799471.jpg?v=1750395725",
    "Utensils/Cutlery": "https://m.media-amazon.com/images/I/81lTodVY8rL.jpg"
}

