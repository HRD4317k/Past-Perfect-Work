const json = {
  "title": "Past Perfect: Pricing Preference Survey",
  "description": "Help us tailor second-hand product prices to better fit your campus community. Your input ensures smarter deals and fairer listings for everyone.",
  "pages": [
    {
      "name": "page1",
      "elements": [
        {
          "type": "boolean",
          "name": "question1",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Wooden Chair?"
        },
        {
          "type": "text",
          "name": "2/Hostel Essentials/Wooden Chair/1/4/2000",
          "visibleIf": "{question1} = true",
          "title": "How much would you pay for a 4-year-old Wooden Chair (originally \u20b92000)?",
          "description": "Moderate signs of use, slightly faded or scratched.",
          "inputType": "number",
          "min": 200.0,
          "max": 1800.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page2",
      "elements": [
        {
          "type": "boolean",
          "name": "question3",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Monitor?"
        },
        {
          "type": "text",
          "name": "4/Electronics/Monitor/1/3/5000",
          "visibleIf": "{question3} = true",
          "title": "How much would you pay for a 3-year-old Monitor (originally \u20b95000)?",
          "description": "Fully functional with light wear or minor cosmetic marks.",
          "inputType": "number",
          "min": 500.0,
          "max": 4500.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page3",
      "elements": [
        {
          "type": "boolean",
          "name": "question5",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Lab Coat?"
        },
        {
          "type": "text",
          "name": "6/Personal Accessories/Lab Coat/0/4/350",
          "visibleIf": "{question5} = true",
          "title": "How much would you pay for a 4-year-old Lab Coat (originally \u20b9350)?",
          "description": "New condition bags, wallets, or belts, no creases or scuffs.",
          "inputType": "number",
          "min": 35.0,
          "max": 315.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page4",
      "elements": [
        {
          "type": "boolean",
          "name": "question7",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Utensils/Cutlery?"
        },
        {
          "type": "text",
          "name": "8/Academic Accessories/Utensils/Cutlery/2/4/400",
          "visibleIf": "{question7} = true",
          "title": "How much would you pay for a 4-year-old Utensils/Cutlery (originally \u20b9400)?",
          "description": "Worn-out or heavily used, some tools may need minor fixing.",
          "inputType": "number",
          "min": 40.0,
          "max": 360.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page5",
      "elements": [
        {
          "type": "boolean",
          "name": "question9",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Whiteboard?"
        },
        {
          "type": "text",
          "name": "10/Academic Accessories/Whiteboard/0/4/400",
          "visibleIf": "{question9} = true",
          "title": "How much would you pay for a 4-year-old Whiteboard (originally \u20b9400)?",
          "description": "Unused or like-new stationery, calculators, or lab tools.",
          "inputType": "number",
          "min": 40.0,
          "max": 360.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page6",
      "elements": [
        {
          "type": "boolean",
          "name": "question11",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Study Lamp?"
        },
        {
          "type": "text",
          "name": "12/Academic Accessories/Study Lamp/2/3/400",
          "visibleIf": "{question11} = true",
          "title": "How much would you pay for a 3-year-old Study Lamp (originally \u20b9400)?",
          "description": "Worn-out or heavily used, some tools may need minor fixing.",
          "inputType": "number",
          "min": 40.0,
          "max": 360.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page7",
      "elements": [
        {
          "type": "boolean",
          "name": "question13",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Study Lamp?"
        },
        {
          "type": "text",
          "name": "14/Academic Accessories/Study Lamp/0/4/300",
          "visibleIf": "{question13} = true",
          "title": "How much would you pay for a 4-year-old Study Lamp (originally \u20b9300)?",
          "description": "Unused or like-new stationery, calculators, or lab tools.",
          "inputType": "number",
          "min": 30.0,
          "max": 270.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page8",
      "elements": [
        {
          "type": "boolean",
          "name": "question15",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Extension Cord?"
        },
        {
          "type": "text",
          "name": "16/Electronics/Extension Cord/0/4/1500",
          "visibleIf": "{question15} = true",
          "title": "How much would you pay for a 4-year-old Extension Cord (originally \u20b91500)?",
          "description": "New or barely used with original packaging, no scratches.",
          "inputType": "number",
          "min": 150.0,
          "max": 1350.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page9",
      "elements": [
        {
          "type": "boolean",
          "name": "question17",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Power Bank?"
        },
        {
          "type": "text",
          "name": "18/Electronics/Power Bank/2/4/800",
          "visibleIf": "{question17} = true",
          "title": "How much would you pay for a 4-year-old Power Bank (originally \u20b9800)?",
          "description": "Frequent usage evident, noticeable scratches or aging.",
          "inputType": "number",
          "min": 80.0,
          "max": 720.0,
          "step": 10
        }
      ]
    },
    {
      "name": "page10",
      "elements": [
        {
          "type": "boolean",
          "name": "question19",
          "defaultValue": "false",
          "isRequired": true,
          "labelFalse": "No",
          "title": "Are you interested in buying Mosquito Nets/Rackets?"
        },
        {
          "type": "text",
          "name": "20/Academic Accessories/Mosquito Nets/Rackets/1/4/750",
          "visibleIf": "{question19} = true",
          "title": "How much would you pay for a 4-year-old Mosquito Nets/Rackets (originally \u20b9750)?",
          "description": "Functional with minor signs of use like scuffs or ink marks.",
          "inputType": "number",
          "min": 75.0,
          "max": 675.0,
          "step": 10
        }
      ]
    }
  ],
  "showPrevButton": false,
  "showProgressBar": true,
  "headerView": "advanced"
};