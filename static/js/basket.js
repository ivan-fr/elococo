// From IB - {% now "Y" %}
let basket_modal = document.getElementById('basket-modal');
let basket_modal_showed = false;
let basket_save_button = false;
let url_get_basket = document.getElementById("basket_urls").getAttribute("data-basket-url-1");
let url_get_booking = document.getElementById("basket_urls").getAttribute("data-basket-url-2");
let httpRequest = new XMLHttpRequest();
let spinner = basket_modal.querySelector(".modal-body").cloneNode(true);
let modal_footer_clone = basket_modal.querySelector(".modal-footer").cloneNode(true);
let modal_form_container = document.getElementById("basket-form");

function add_save_button(footer) {
    return function listener() {
        if (basket_save_button) {
            return;
        }

        basket_save_button = true;
        let submit_button = document.createElement("button");
        submit_button.setAttribute("type", "submit")
        submit_button.classList.add("btn", "btn-info", "text-white");
        text = document.createTextNode("Sauvegarder les changements");
        submit_button.appendChild(text);
        footer.appendChild(submit_button);
        footer.classList.remove("is-hidden");
    }
}

function create_form_csrf(csrf, url) {
    let form = document.createElement("form");
    form.setAttribute("action", url);
    form.setAttribute("method", "post");
    form.appendChild(csrf_input(csrf));
    return form;
}

function csrf_input(csrf) {
    let input_csrf = document.createElement("input");
    input_csrf.setAttribute("type", "hidden");
    input_csrf.setAttribute("name", "csrfmiddlewaretoken");
    input_csrf.setAttribute("value", csrf);
    return input_csrf
}

function status200() {
    let basket = httpRequest.response;
    let modal_body = basket_modal.querySelector(":scope .modal-body");

    if (basket.hasOwnProperty("form")) {
        let modal_form_container_footer = modal_footer_clone.cloneNode();
        basket_save_button = false;
        modal_form_container.innerHTML = basket["form"];
        modal_form_container.querySelector(":scope form").insertAdjacentElement("beforeend", modal_form_container_footer);
        modal_form_container_footer.classList.add("btn", "is-hidden");

        let select = modal_form_container.querySelector(":scope form select");
        let input = modal_form_container.querySelector(":scope form input");
        select.addEventListener("change", add_save_button(modal_form_container_footer));
        input.addEventListener("change", add_save_button(modal_form_container_footer));
        modal_form_container.querySelector(":scope form").addEventListener("submit", post_basket);

        get_booking();
    } else {
        let div = document.createElement("div");
        let text = document.createTextNode("Votre panier est vide.");
        div.appendChild(text);
        modal_body.innerHTML = "";
        modal_body.appendChild(div);
    }

    document.getElementById("basket_len").textContent = Object.keys(basket).length;
}

function onload_bakset() {
    if (httpRequest.readyState === XMLHttpRequest.DONE) {
        if (httpRequest.status === 200) {
            setTimeout(status200, 500);
        } else {
            alert('Il y a eu un problème avec la requête.');
        }
    }
}

function onload_booking() {
    if (httpRequest.readyState === XMLHttpRequest.DONE) {
        if (httpRequest.status === 200) {
            let data = httpRequest.response;
            if (data.hasOwnProperty("redirect")) {
                window.location.href = data["redirect"];
            } else if (data.hasOwnProperty("reload")) {
                window.location.reload();
            } else {
                let modal_form_container_footer = modal_footer_clone.cloneNode(true);
                modal_form_container.appendChild(modal_form_container_footer);

                let btn_spinner = document.createElement("button");
                btn_spinner.classList.add("btn", "btn-primary");
                btn_spinner.innerHTML = '<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span><span class="visually-hidden">Loading...</span>';
                modal_form_container_footer.appendChild(btn_spinner);

                setTimeout(function () {
                    let form = create_form_csrf(data["csrf_token"], url_get_booking);
                    let button_validation = document.createElement("button");
                    button_validation.setAttribute("type", "submit");
                    button_validation.classList.add("btn", "btn-success");
                    text = document.createTextNode("Reserver");
                    button_validation.appendChild(text);
                    form.appendChild(button_validation);
                    form.addEventListener("submit", post_booking);
                    modal_form_container_footer.removeChild(btn_spinner);

                    if (data.hasOwnProperty("form_errors")) {
                        form.insertAdjacentHTML("afterbegin", data["form_errors"]);
                    }

                    modal_form_container_footer.appendChild(form);
                }, 500);
            }
        } else {
            alert('Il y a eu un problème avec la requête.');
        }
    }
}

function get_booking() {
    if (!httpRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    httpRequest.onload = onload_booking;
    httpRequest.open('GET', url_get_booking);
    httpRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    httpRequest.responseType = 'json';
    httpRequest.send();
}

function get_basket() {
    if (basket_modal_showed) {
        return false;
    }

    basket_modal_showed = true;

    if (!httpRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    httpRequest.onload = onload_bakset;
    httpRequest.open('GET', url_get_basket);
    httpRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    httpRequest.responseType = 'json';
    httpRequest.send();
}

function post_basket(event) {
    event.preventDefault();
    if (!httpRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    modal_form_container.innerHTML = "";
    modal_form_container.appendChild(spinner.cloneNode(true));
    modal_form_container.appendChild(modal_footer_clone.cloneNode(true));

    httpRequest.onload = onload_bakset;
    httpRequest.open('POST', url_get_basket, true);
    httpRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    httpRequest.responseType = 'json';
    httpRequest.send(new FormData(event.currentTarget));
}

function post_booking(event) {
    event.preventDefault();
    if (!httpRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    httpRequest.onload = onload_booking;
    httpRequest.open('POST', url_get_booking, true);
    httpRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    httpRequest.responseType = 'json';
    httpRequest.send(new FormData(event.currentTarget));
}

basket_modal.addEventListener('show.bs.modal', get_basket);