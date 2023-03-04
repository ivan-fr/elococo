let fill_next_config = document.getElementById("fill_next_config");
let form_delivery_address = document.getElementById("delivery_address");
i = 0;
list_text = [fill_next_config.innerText, "Facturation diffère de la livraison"]
fill_next_config.addEventListener("click", (event) => {
    form_delivery_address.classList.toggle("expand");
    i = (i + 1) % list_text.length;
    fill_next_config.innerText = list_text[i];
})