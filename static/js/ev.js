document.addEventListener('DOMContentLoaded', function () {
    if (typeof noUiSlider !== 'undefined') {
        // Year Slider
        const yearSlider = document.getElementById('year-slider');
        if (yearSlider) {
            noUiSlider.create(yearSlider, {
                start: [currentFilters.year.min, currentFilters.year.max],
                connect: true,
                range: {
                    'min': filterOptions.years[0],
                    'max': filterOptions.years[filterOptions.years.length - 1]
                },
                step: 1,
                format: {
                    to: function (value) {
                        return Math.round(value);
                    },
                    from: function (value) {
                        return Math.round(value);
                    }
                }
            });

            const yearMinInput = document.getElementById('year_min');
            const yearMaxInput = document.getElementById('year_max');
            const yearMinValue = document.getElementById('year-min-value');
            const yearMaxValue = document.getElementById('year-max-value');

            yearSlider.noUiSlider.on('update', function (values, handle) {
                if (handle === 0) {
                    yearMinInput.value = values[0];
                    yearMinValue.textContent = values[0];
                }
                if (handle === 1) {
                    yearMaxInput.value = values[1];
                    yearMaxValue.textContent = values[1];
                }
            });
        }

        // Price Slider
        const priceSlider = document.getElementById('price-slider');
        if (priceSlider) {
            noUiSlider.create(priceSlider, {
                start: [currentFilters.price.min, currentFilters.price.max],
                connect: true,
                range: {
                    'min': filterOptions.prices.min,
                    'max': filterOptions.prices.max
                },
                step: 1000,
                format: {
                    to: function (value) {
                        return Math.round(value);
                    },
                    from: function (value) {
                        return Math.round(value);
                    }
                }
            });

            const priceMinInput = document.getElementById('price_min');
            const priceMaxInput = document.getElementById('price_max');
            const priceMinValue = document.getElementById('price-min-value');
            const priceMaxValue = document.getElementById('price-max-value');

            priceSlider.noUiSlider.on('update', function (values, handle) {
                if (handle === 0) {
                    priceMinInput.value = values[0];
                    priceMinValue.textContent = '$' + Math.round(values[0]).toLocaleString();
                }
                if (handle === 1) {
                    priceMaxInput.value = values[1];
                    priceMaxValue.textContent = '$' + Math.round(values[1]).toLocaleString();
                }
            });
        }
    }
});