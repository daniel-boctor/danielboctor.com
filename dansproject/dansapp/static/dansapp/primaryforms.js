document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('id_granularity').addEventListener("change", () => granularity_field(event.target.value));
    granularity_field(document.getElementById('id_granularity').value);

    window.formset_block = document.querySelector(".portfolio_form")
    window.tickerform_block = document.querySelector("#tickerform_block")
    addForm("");
    document.getElementById('id_type').addEventListener("change", () => toggle_type(event.target.value));
    toggle_type(document.getElementById('id_type').value);
    document.querySelector('#id_form-0-ticker1').setAttribute('required', '');
    document.querySelector('#id_form-0-weight1').setAttribute('required', '');
});
function toggle_type(type) {
    let meta_block = document.querySelector(".meta_form")
    if (type === "formset_block") {
        document.querySelector("#tickerform_block").remove()
        meta_block.after(window.formset_block);
        document.querySelector("#id_form-TOTAL_FORMS").setAttribute('value', `${1}`)
        document.querySelector("#add_form").style.display = 'inline-block';
        document.querySelector('#select_portfolio').style.display = 'block';
    }
    if (type === "tickerform_block") {
        document.querySelectorAll(".portfolio_form").forEach(e => e.remove());
        meta_block.after(window.tickerform_block);
        document.querySelector("#add_form").style.display = 'none';
        document.querySelector("#remove_form").style.display = 'none';
        document.querySelector('#select_portfolio').style.display = 'none';
    }
}
function granularity_field(type) {
    if (type === "1d") {
        type = "date"
        placeholder = "YYYY-MM-DD"
    } else if (type === "1mo") {
        type = "month"
        placeholder = "YYYY-MM"
    }
    document.getElementById('id_datestamp_start').type = type;
    document.getElementById('id_datestamp_start').placeholder = placeholder;
    document.getElementById('id_datestamp_end').type = type;
    document.getElementById('id_datestamp_end').placeholder = placeholder;
}
function toggle_advanced(checked) {
    if (checked) {
        document.getElementById('advanced').style.display = 'block';
        document.getElementById('basic').style.display = 'none';
    } else {
        document.getElementById('advanced').style.display = 'none';
        document.getElementById('basic').style.display = 'block';
    }
}
function addForm(event, csv=false) {
    //add or remove new portfolio
    let portfolioForm = document.querySelectorAll(".portfolio_form")
    let totalForms = document.querySelector("#id_form-TOTAL_FORMS")
    let formNum = portfolioForm.length-1
    if (event == "add_form") {
        let newForm = portfolioForm[0].cloneNode(true)
        let formRegex = RegExp(`form-(\\d){1}-`,'g')
        formNum++
        newForm.innerHTML = newForm.innerHTML.replace(formRegex, `form-${formNum}-`)
        portfolioForm[formNum-1].after(newForm);
        document.querySelector(`#id_form-${formNum}-name`).setAttribute('value', "")
        clear_form(formNum)
    } else if (event == "remove_form") {
        portfolioForm[formNum].remove()
        formNum--
    } else if (event != "") {
        if (csv == true) {
            document.querySelector('#select_csv').value = 'default'
            if (event != "No saved CSVs! Head to your account page to get started.") {
                document.querySelector('.csv_parent_block').style.display = 'block';
                csv_num = document.querySelectorAll('.csv_input').length + 1
                document.querySelector('#csv_block').insertAdjacentHTML('beforeend', `<tr><td>Saved CSV - ${csv_num}</td><td><input name="csv-${csv_num}" class="form-control csv_input" id="csv-${csv_num}"></td></tr>`);
                document.querySelector(`#csv-${csv_num}`).setAttribute('value', event)
                document.querySelector('#id_form-0-ticker1').required = false;
                document.querySelector('#id_form-0-weight1').required = false;
            }
        } else {
            document.querySelector('#select_portfolio').value = 'default'
            fetch(`/portfolio_api/${event}`, {
                method: 'POST',
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                mode: "same-origin"
            })
            .then(response => response.json())
            .then(result => {
                for (const [key, value] of Object.entries(result)) {
                    document.querySelector(`#id_form-${formNum}-${key}`).setAttribute('value', value)
                }
            });
        }
    }
    totalForms.setAttribute('value', `${formNum+1}`)
    if (formNum >= 4) {
        document.querySelector("#add_form").style.display = 'none';
    } else {
        document.querySelector("#add_form").style.display = 'inline-block';
    }
    if (formNum == 0) {
        document.querySelector("#remove_form").style.display = 'none';
    } else {
        document.querySelector("#remove_form").style.display = 'inline-block';
    }
    return false;
}
function clear_form(formNum) {
    document.querySelector(`#id_form-${formNum}-name`).setAttribute('value', "")
    for (i=1; i<=8; i++) {
        document.querySelector(`#id_form-${formNum}-ticker${i}`).setAttribute('value', "")
        document.querySelector(`#id_form-${formNum}-weight${i}`).setAttribute('value', "")
    }
}
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}