let fill_next_config = document.getElementById("fill_next_config");
let form_facturation_address = document.getElementById("facturation_address");
i = 0;
list_text = [fill_next_config.textContent, "Facturation diffère de la livraison"]
fill_next_config.addEventListener("click", (event) => {
    form_facturation_address.classList.toggle("is-hidden");
    i = (i + 1) % list_text.length;
    fill_next_config.innerText = list_text[i];
})