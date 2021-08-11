import React, { useContext } from 'react';
import { doubleRangeContext } from '../contexts/double_range';


function DoubleRange() {
    const {min, max} = useContext(doubleRangeContext)

    return <nav className="range_filter">
        <ul>
            <li>
                <div className="dr_value_left text-left" data-dr-left={min}>
                    {min} €
                </div>
                <div className="dr_main">
                    <div className="dr_wrapper">
                        <div className="dr_box"></div>
                    </div>
                    <div className="dr_wrapper">
                        <div className="dr_box"></div>
                    </div>
                    <div className="double_range_temoin">
                    </div>
                    <div className="double_range">
                    </div>
                </div>
                <div className="dr_value_right text-right" data-dr-right={max}>
                    {max} €
                </div>
            </li>
        </ul>
    </nav>
}

export default DoubleRange;
