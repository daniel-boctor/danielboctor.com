function fetch_spreads(suffix="TO", ticker="DLR", market="C") {
    url = `https://www.stockwatch.com/Quote/Detail?${market}:${ticker}`

    fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(url)}`)
    .then(response => {
        if (response.ok) return response.json()
        throw new Error('Network response was not ok.')
    })
    .then(data => {
        b_pos = data.contents.search("UpdB")
        a_pos = data.contents.search("UpdA")
        
        if (b_pos === -1) {
            document.querySelector('#form-container').insertAdjacentHTML('afterbegin', 
            `<div class="alert alert-danger alert-dismissible sticky-top fade show" role="alert">
                <strong>Error:</strong> ${ticker} could not be found.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`);
            return
        }
        bid = data.contents.slice(b_pos+6, b_pos+data.contents.slice(b_pos).search("<"))
        ask = data.contents.slice(a_pos+6, a_pos+data.contents.slice(a_pos).search("<"))
        
        document.querySelector(`#${suffix}-BID`).innerHTML = bid
        document.querySelector(`#${suffix}-ASK`).innerHTML = ask
        document.querySelector(`#td_${suffix}_label`).innerHTML = ticker
    });
}

function refresh() {
    fetch_spreads(suffix="TO", ticker=document.querySelector("#cad_ticker").value, market=document.querySelector("#cad_market").value)
    fetch_spreads(suffix="U", ticker=document.querySelector("#usd_ticker").value, market=document.querySelector("#usd_market").value)
}

$(document).ready(function() {
    refresh()
    fetch(`https://www.bankofcanada.ca/valet/observations/FXUSDCAD?recent=1`)
    .then(response => {
        if (response.ok) return response.json()
        throw new Error('Network response was not ok.')
    })
    .then(data => {
        present_fx_info = [data.observations[0].d, data.observations[0].FXUSDCAD.v]
    });
    document.querySelector("#id_buy_FX").required = false;
    document.querySelector("#id_sell_FX").required = false;
    document.querySelector("#id_initial").required = false;
    $('#post-form').submit(function(event) {
        event.preventDefault()
        document.querySelectorAll(".FX_lookup").forEach(function (elem) {
            if (elem.value === "") {
                document.querySelector(`#id_${elem.id}`).value = present_fx_info[1]
                elem.value = present_fx_info[0]
            }
        })
        if (document.querySelector("#id_initial").value === "") {document.querySelector("#id_initial").value = 10000}
        $.ajax({
            data: $(this).serialize(),
            type: 'POST',
            url: '',
            headers: {
                'X-CSRFToken': getCookie("csrftoken")
            },
            success: function(response) {
                if (Object.keys(response)[0] === "ERROR") {
                    response = response["ERROR"];
                    for (i=0; i<Object.keys(response).length; i++) {
                        document.querySelector('#form-container').insertAdjacentHTML('afterbegin', 
                        `<div class="alert alert-danger alert-dismissible sticky-top fade show" role="alert">
                            <strong>${Object.keys(response)[i]}:</strong> ${response[Object.keys(response)[i]]}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>`);
                    }
                } else {
                    document.querySelectorAll(".alert").forEach(function (elem) {elem.remove()})
                    document.querySelector("#info").style.display = "block";
                    for (i=0; i<Object.keys(response).length; i++) {
                        document.querySelector(`#id_${i}`).innerHTML = response[Object.keys(response)[i]]
                    }
                    //coloring
                    document.querySelector("#id_1").firstChild.childNodes[3].childNodes.forEach(function(elem) {
                        if (elem.tagName === "TR") {
                            if (elem.childNodes[1].innerHTML != "Explicit Costs Incurred") {
                                if (elem.childNodes[3].innerHTML.substring(0, 1) === "-" || elem.childNodes[3].innerHTML.substring(1, 2) === "-") {
                                    elem.childNodes[3].style.color = "red"
                                } else {
                                    elem.childNodes[3].style.color = "green"
                                }
                                if (elem.childNodes.length > 5) {elem.childNodes[5].style.color = "red"}
                            }
                        }
                    })
                }
            }
        });
    });

    document.querySelectorAll(".spread").forEach(function (elem) {
        elem.addEventListener("click", function(event) {
            if (event.currentTarget.childNodes[2].id.substring(0, 1) === "T") {
                document.querySelector(`#id_DLR_TO`).value = event.currentTarget.childNodes[2].innerHTML.replace(',', '')
            } else {
                document.querySelector(`#id_DLR_U_TO`).value = event.currentTarget.childNodes[2].innerHTML.replace(',', '')
            }
        })
    })

    document.querySelectorAll(".FX_lookup").forEach(function (elem) {
        elem.addEventListener("change", function(event) {
            if (event.currentTarget.value != "") {
                fx(event.currentTarget.id, event.currentTarget.value)
            }
        })
    })
    document.querySelector("#id_initial_fx").addEventListener("change", function(event) {
        if (document.querySelector("#td_cad").parentElement.childNodes[1].id.substring(3, 7).toUpperCase() != event.currentTarget.value) {
            td_cad = document.querySelector("#td_cad")
            td_usd = document.querySelector("#td_usd")
            var temp = document.createElement("div");
            td_cad.parentNode.insertBefore(temp, td_cad);
            td_usd.parentNode.insertBefore(td_cad, td_usd);
            temp.parentNode.insertBefore(td_usd, temp);
            temp.parentNode.removeChild(temp);
        }
    })
    document.querySelector("#toggle_descriptions").addEventListener("click", function(event) {
        if (event.currentTarget.checked) {
            var checked = 'block'
        } else {
            var checked = 'none'
        }
        document.querySelectorAll(".description").forEach(function (elem) {
            elem.style.display = checked
        })
    })
});

function fx(target, date) {
    fetch(`https://www.bankofcanada.ca/valet/observations/FXUSDCAD?start_date=${date}&end_date=${date}`)
    .then(response => {
        if (response.ok) return response.json()
        throw new Error('Network response was not ok.')
    })
    .then(data => {
        if (data.observations.length == 0) {
            alert("No data available for the selected date. Data available Jan 2017 - most recent business day. Please see https://www.bankofcanada.ca/ for more info.")
        } else {
            document.querySelector(`#id_${target}`).value = data.observations[0].FXUSDCAD.v
        }
    });
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