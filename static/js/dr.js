let dr = document.querySelector(".dr_main .double_range");
let box_left = document.querySelector(".dr_main .dr_wrapper:nth-of-type(1) .dr_box");
let box_right = document.querySelector(".dr_main .dr_wrapper:nth-of-type(2) .dr_box");
let move_event = null;
let do_add_event_listener_up = true;
let zIndex = 10;

let dr_main = document.querySelector(".dr_main").getBoundingClientRect();

let dr_value_left = document.querySelector(".dr_grid .dr_value_left");
let dr_value_right = document.querySelector(".dr_grid .dr_value_right");

let dr_value_left_init = parseFloat(dr_value_left.getAttribute("data-dr-left").replace(',', '.'));
let dr_value_right_init = parseFloat(dr_value_right.getAttribute("data-dr-right").replace(',', '.'));

let dr_coords_init = dr.getBoundingClientRect()

function lineare(start, end, x) {
    let a = (end - start);
    return x * a + start;
}

function reverse_lineare(start, end, r) {
    let a = (end - start);
    return (r - start) / a;
}

function callback(box, direction) {
    let init_page_x = null;

    let limit_max;
    let limit_min;
    let direction_str;
    let start, end;

    if (direction === 1) {
        direction_str = "right";
        limit_min = 0.;
        limit_max = Math.round(((dr_main.right - box_left.getBoundingClientRect().left) / dr_main.width + Number.EPSILON) * 100) / 100;
        start = dr_value_right_init;
        end = dr_value_left_init;
    } else {
        direction_str = "left";
        limit_min = 0.;
        limit_max = Math.round(((box_right.getBoundingClientRect().right - dr_main.left) / dr_main.width + Number.EPSILON) * 100) / 100;
        start = dr_value_left_init;
        end = dr_value_right_init;
    }

    return function (event) {
        if (init_page_x === null) {
            init_page_x = event.pageX;
        }
        let base_percentage, function_quotion;
        if (direction === 1) {
            function_quotion = Math.ceil;
            base_percentage = Math.max(limit_min, Math.min((dr_main.right - event.pageX) / dr_main.width, limit_max));
        } else {
            function_quotion = Math.floor;
            base_percentage = Math.max(limit_min, Math.min((event.pageX - dr_main.left) / dr_main.width, limit_max));
        }


        let value = lineare(start, end, base_percentage);

        let quotient_relative = function_quotion((value - start) / 2);

        let value_target;
        value_target = start + 2 * quotient_relative;

        let back_base_percentage = reverse_lineare(start, end, value_target);

        let percentage = Math.max(limit_min, Math.min(back_base_percentage, limit_max));

        let distance_value = lineare(start, end, percentage);

        if (direction === 1) {
            distance_value = Math.round((distance_value + Number.EPSILON) * 100) / 100
            dr_value_right.setAttribute("data-dr-right", `${distance_value}`);
            dr_value_right.textContent = `${distance_value} €`;
            box_right.style.backgroundColor = null;
        } else {
            distance_value = Math.round((distance_value + Number.EPSILON) * 100) / 100
            dr_value_left.setAttribute("data-dr-left", `${distance_value}`);
            dr_value_left.textContent = `${distance_value} €`;
            box_left.style.backgroundColor = null;
        }

        box.parentElement.style.setProperty(
            direction_str, `max(0px, ${percentage * 100}% - ${box_right.getBoundingClientRect().width}px)`
        );

        let px_2 = Math.abs((box_right.getBoundingClientRect().right - box_left.getBoundingClientRect().left - box_left.getBoundingClientRect().width));
        let px_3 = (box_left.getBoundingClientRect().left - dr_coords_init.left + box_left.getBoundingClientRect().width);
        dr.style.width = `${px_2}px`;
        dr.style.left = `${px_3}px`;

        let pass = px_2 > 1e-1;

        if (direction === 1) {
            if (!pass) {
                box_right.style.backgroundColor = "#ff7474"
            }
        } else {
            if (!pass) {
                box_left.style.backgroundColor = "#ff7474";
            }
        }

        if (do_add_event_listener_up) {
            document.addEventListener("pointerup", up);
            do_add_event_listener_up = false;
        }
    };
}

function up() {
    document.removeEventListener("pointermove", move_event);
    document.body.style.cursor = null;
    document.body.style.userSelect = null;
    move_event = null;
    box_right.style.backgroundColor = null;
    box_left.style.backgroundColor = null;
    do_add_event_listener_up = true;
}

box_left.addEventListener("pointerdown", function (event) {
    event.currentTarget.parentElement.style.zIndex = `${zIndex}`;
    zIndex++;
    move_event = callback(event.currentTarget, 0);
    document.body.style.cursor = "move";
    document.body.style.userSelect = "none";
    document.addEventListener("pointermove", move_event);
})

box_right.addEventListener("pointerdown", function (event) {
    event.currentTarget.parentElement.style.zIndex = `${zIndex}`;
    zIndex++;
    move_event = callback(event.currentTarget, 1);
    document.body.style.cursor = "move";
    document.body.style.userSelect = "none";
    document.addEventListener("pointermove", move_event);
})
