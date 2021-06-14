function dr(dr_grid, on_up) {
    let dr = dr_grid.querySelector(".dr_main .double_range");
    let dr_temoin = dr_grid.querySelector(".dr_main .double_range_temoin");
    let box_left = dr_grid.querySelector(".dr_main .dr_wrapper:nth-of-type(1) .dr_box");
    let box_right = dr_grid.querySelector(".dr_main .dr_wrapper:nth-of-type(2) .dr_box");
    let zIndex = 10;

    let dr_main = dr_grid.querySelector(".dr_main").getBoundingClientRect();

    let dr_value_left = dr_grid.querySelector(".dr_value_left");
    let dr_value_right = dr_grid.querySelector(".dr_value_right");

    let dr_value_left_init = parseFloat(dr_value_left.getAttribute("data-dr-left").replace(',', '.'));
    let dr_value_right_init = parseFloat(dr_value_right.getAttribute("data-dr-right").replace(',', '.'));

    let dr_chosen_value_left_init = dr_value_left.getAttribute("data-dr-left").replace(',', '.');
    let dr_chosen_value_right_init = dr_value_right.getAttribute("data-dr-right").replace(',', '.');


    function linear(start, end, x) {
        let a = (end - start);
        return x * a + start;
    }

    function reverse_linear(start, end, r) {
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
            start = dr_value_right_init;
            end = dr_value_left_init;
            limit_max = Math.round(((dr_main.right - box_left.getBoundingClientRect().left) / dr_main.width + Number.EPSILON) * 100) / 100;
        } else {
            direction_str = "left";
            limit_min = 0.;
            start = dr_value_left_init;
            end = dr_value_right_init;
            limit_max = Math.round(((box_right.getBoundingClientRect().right - dr_main.left) / dr_main.width + Number.EPSILON) * 100) / 100;
        }

        return function (event) {
            if (init_page_x === null) {
                init_page_x = event.pageX;
            }
            let base_percentage, function_quotient;
            if (direction === 1) {
                function_quotient = Math.ceil;
                base_percentage = Math.max(limit_min, Math.min((dr_main.right - event.pageX) / dr_main.width, limit_max));
            } else {
                function_quotient = Math.floor;
                base_percentage = Math.max(limit_min, Math.min((event.pageX - dr_main.left) / dr_main.width, limit_max));
            }

            let value = linear(start, end, base_percentage);
            let quotient_relative = function_quotient((value - start) / 2);

            let value_target_end;

            if (direction === 1) {
                value_target_end = parseFloat(dr_value_left.getAttribute("data-dr-left").replace(',', '.')) + 2;
                limit_max = reverse_linear(start, end, value_target_end);
            } else {
                value_target_end = parseFloat(dr_value_right.getAttribute("data-dr-right").replace(',', '.')) - 2;
                limit_max = reverse_linear(start, end, value_target_end);
            }

            let value_target = start + 2 * quotient_relative;

            let back_base_percentage = reverse_linear(start, end, value_target);

            let percentage = Math.max(limit_min, Math.min(back_base_percentage, limit_max));

            let distance_value = linear(start, end, percentage);

            if (direction === 1) {
                distance_value = Math.round((distance_value + Number.EPSILON) * 100) / 100
                dr_value_right.setAttribute("data-dr-right", `${distance_value}`);
                dr_value_right.textContent = `${distance_value.toString().replace(".", ",")} €`;
                box_right.style.backgroundColor = null;
            } else {
                distance_value = Math.round((distance_value + Number.EPSILON) * 100) / 100
                dr_value_left.setAttribute("data-dr-left", `${distance_value}`);
                dr_value_left.textContent = `${distance_value.toString().replace(".", ",")} €`;
                box_left.style.backgroundColor = null;
            }

            box.parentElement.style.setProperty(
                direction_str, `max(0px, ${percentage * 100}% - ${box_right.getBoundingClientRect().width}px)`
            );

            let px_2 = Math.abs((box_right.getBoundingClientRect().right - box_left.getBoundingClientRect().left - box_left.getBoundingClientRect().width));
            let px_3 = (box_left.getBoundingClientRect().left - dr_temoin.getBoundingClientRect().left + box_left.getBoundingClientRect().width);
            dr.style.width = `${px_2}px`;
            dr.style.left = `${px_3}px`;
        };
    }

    function callback_up(move_event) {
        return function up() {
            document.removeEventListener("pointermove", move_event);
            document.body.style.cursor = null;
            document.body.style.userSelect = null;
            move_event = null;
            box_right.style.backgroundColor = null;
            box_left.style.backgroundColor = null;

            let left = dr_value_left.getAttribute("data-dr-left").replace(",", ".");
            let right = dr_value_right.getAttribute("data-dr-right").replace(",", ".")

            if (left !== dr_chosen_value_left_init || right !== dr_chosen_value_right_init) {
                dr_chosen_value_right_init = right
                dr_chosen_value_left_init = left

                on_up(
                    dr_chosen_value_left_init,
                    dr_chosen_value_right_init
                );
            }

            document.removeEventListener("pointerup", up);
        }
    }

    function callback_down(direction) {
        return function down(event) {
            event.currentTarget.parentElement.style.zIndex = `${zIndex}`;
            zIndex++;
            let move_event = callback(event.currentTarget, direction);
            document.body.style.cursor = "move";
            document.body.style.userSelect = "none";
            document.addEventListener("pointermove", move_event);
            document.addEventListener("pointerup", callback_up(move_event));
        }
    }

    box_left.addEventListener("pointerdown", callback_down(0));

    box_right.addEventListener("pointerdown", callback_down(1));
}