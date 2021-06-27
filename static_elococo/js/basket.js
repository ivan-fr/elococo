// From IB
let XmlHTTPRequest = new XMLHttpRequest();
let url_get_promo;
let url_get_book;

if (document.getElementById("basket_urls") !== null) {
    url_get_book = document.getElementById("basket_urls").getAttribute("data-basket-url-2");
    url_get_promo = document.getElementById("basket_urls").getAttribute("data-basket-url-3");
    let basket_save_button = false;

    function add_save_button(footer) {
        return function listener() {
            if (basket_save_button) {
                return;
            }

            basket_save_button = true

            let submit_button = document.createElement("button");
            submit_button.setAttribute("type", "submit")
            let text = document.createTextNode("Sauvegarder les changements");
            submit_button.appendChild(text);
            footer.appendChild(submit_button);
        }
    }

    let footer = document.querySelector("#submit_basket")
    let inputs = document.querySelectorAll("form#basket_form input")
    for (const inputElement of inputs) {
        inputElement.addEventListener("change", add_save_button(footer));
    }
    let selects = document.querySelectorAll("form#basket_form select")
    for (const selectElement of selects) {
        selectElement.addEventListener("change", add_save_button(footer));
    }

    get_promo()
}

function get_promo() {
    if (!XmlHTTPRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    XmlHTTPRequest.onload = onload_promo;
    XmlHTTPRequest.open('GET', url_get_promo);
    XmlHTTPRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    XmlHTTPRequest.responseType = 'json';
    XmlHTTPRequest.send();
}

function onload_promo() {
    if (XmlHTTPRequest.readyState === XMLHttpRequest.DONE) {
        if (XmlHTTPRequest.status === 200) {
            let data = XmlHTTPRequest.response;
            if (data.hasOwnProperty("form_promo")) {
                document.getElementById("promo_form").innerHTML = data["form_promo"]
                document.getElementById("promo_form").querySelector("form").addEventListener("submit", post_promo)
                get_book()
            } else {
                window.location.reload()
            }
        } else {
            alert('Il y a eu un problème avec la requête.')
        }
    }
}

function post_promo(event) {
    event.preventDefault()
    if (!XmlHTTPRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP')
        return false;
    }

    let form = event.currentTarget
    form.parentElement.removeChild(form)

    XmlHTTPRequest.onload = onload_promo
    XmlHTTPRequest.open('POST', url_get_promo, true)
    XmlHTTPRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    XmlHTTPRequest.responseType = 'json'
    XmlHTTPRequest.send(new FormData(event.currentTarget))
}


function get_book() {
    if (!XmlHTTPRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP')
        return false;
    }

    XmlHTTPRequest.onload = onload_book;
    XmlHTTPRequest.open('GET', url_get_book);
    XmlHTTPRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest')
    XmlHTTPRequest.responseType = 'json';
    XmlHTTPRequest.send();
}

function onload_book() {
    if (XmlHTTPRequest.readyState === XMLHttpRequest.DONE) {
        if (XmlHTTPRequest.status === 200) {
            let data = XmlHTTPRequest.response;
            if (data.hasOwnProperty("form_book")) {
                document.getElementById("book_form").innerHTML = data["form_book"]
                document.getElementById("book_form").querySelector("form").addEventListener("submit", post_book)
            } else if (data.hasOwnProperty("redirect")) {
                window.location.href = data["redirect"]
            }
        } else {
            alert('Il y a eu un problème avec la requête.')
        }
    }
}

function post_book(event) {
    event.preventDefault()
    if (!XmlHTTPRequest) {
        alert('Abandon :( Impossible de créer une instance de XMLHTTP');
        return false;
    }

    if (!confirm("Etes vous sûr de vouloir réserver le panier ? Vous ne pourrez pas consitué un autre panier pendant une certaine durée si le paiement n'est pas effectué.")) {
        return false;
    }

    let form = event.currentTarget;
    form.parentElement.removeChild(form);

    XmlHTTPRequest.onload = onload_book;
    XmlHTTPRequest.open('POST', url_get_book, true);
    XmlHTTPRequest.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    XmlHTTPRequest.responseType = 'json';
    XmlHTTPRequest.send(new FormData(event.currentTarget));

    return true;
}
