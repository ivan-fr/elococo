// From IB
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