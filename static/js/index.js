const survey = new Survey.Model(json);
survey.applyTheme(themeJson);
survey.onComplete.add((sender) => {
    const data = sender.data;
    data.ref = referrer;  // add referrer to data

    fetch("/submit-survey", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (res.ok) {
            alert("Survey submitted successfully!");
            window.location.href = "/register";
        } else {
            alert("Error submitting survey.");
        }
    })
    .catch(err => {
        alert("Fetch error: " + err);
    });
});

survey.render(document.getElementById("surveyElement"));