/* --------------------------------------------------------------------------
 * File        : config-theme.js
 * Author      : indonez
 * Author URI  : http://www.indonez.com
 *
 * Indonez Copyright 2020 All Rights Reserved.
 * -------------------------------------------------------------------------- 
 * javascript handle initialization
    1. Slideshow
    2. Testimoni carousel
    3  Mobile nav button
    4. Market widget
 * -------------------------------------------------------------------------- */

    'use strict';

    const HomepageApp = {
        //----------- 1. Slideshow -----------
        theme_slideshow: function() {
            const path = location.pathname;

            new CarouselConfig({
                element: '#slideshow',              // carousel element id
                fadeTransition: false,              // default is slide, use 'true' if want use fade effect
                interval: 6000,                     // interval between change slide
                control: {
                    type: 'button',                 // the options is: 'button', 'indicator' and 'both'
                    onHover: true                   // control appears when hover in careousel element
                },
                height: {                           // height for every devices
                    desktop: '723px',
                    tablet: '493px',
                    phone: '512px'
                }
            }).init();

            if(path.includes('homepage2') || path.includes('homepage4')) {
                new CarouselConfig({
                    element: '#slideshow',          // carousel element id
                    fadeTransition: false,          // default is slide, use 'true' if want use fade effect
                    interval: 6000,                 // interval between change slide
                    control: {
                        type: 'button',             // the options is: 'button', 'indicator' and 'both'
                        onHover: true               // control appears when hover in careousel element
                    },
                    height: {                       // height for every devices
                        desktop: '604px',
                        tablet: '463px',
                        phone: '476px'
                    }
                }).init();
            }
        },
        //----------- 2. Testimoni carousel -----------
        theme_testimoni: function() {
            new CarouselConfig({
                element: '#testimoni',              // carousel element id
                fadeTransition: false,              // default is slide, use 'true' if want use fade effect
                interval: 9000,                     // interval between change slide
                control: {
                    type: 'indicator',              // the options is: 'button', 'indicator' and 'both'
                    onHover: false                  // control appears when hover in careousel element
                },
                height: {                           // height for every devices
                    desktop: '238px',
                    tablet: '260px',
                    phone: '320px'
                }
            }).init();
        },
        //---------- 3. Mobile nav button -----------
        theme_mobilenav: function() {
            new MobileNavbar({
                addonButtons: true,                 // options to use addon buttons, set it "false" if you won't use addon buttons
                buttons: [
                    {
                        name: 'Login',              // button name
                        url: '',                    // button url
                        type: 'primary',            // button type (default, primary, secondary, danger, text)
                        icon: 'sign-in-alt'         // button icon, you can use all icons from here : https://fontawesome.com/icons?d=gallery&s=solid&m=free
                    },
                ]
            }).init();
        },
        //---------- 4. Market widget -----------
        theme_marketwidget: function() {
            new MarketWidget({
                variants: 'ticker-tape',            // market widget variant (market-list, jumbo-chart, mini-chart, ticker-tape, ticker)
                theme: 'light',                     // widget theme (dark, light)
                data: 'data/ticker-tape.json',      // url data source
                logo: false                         // set false if want hide symbol logo
            }).init()
            
            new MarketWidget({
                variants: 'mini-chart',             // market widget variant (market-list, jumbo-chart, mini-chart, ticker-tape, ticker)
                height: 100,                        // widget height
                theme: 'light',                     // widget theme (dark, light)
                colors: ['#22AB94', '#F7525F'],     // chart color in array, first index is up condition and the last index is down condition
                data: 'data/mini-chart.json'        // url data source
            }).init()

            new MarketWidget({
                variants: 'market-list',            // market widget variant (market-list, jumbo-chart, mini-chart, ticker-tape, ticker)
                theme: 'light',                     // widget theme (dark, light)
                data: 'data/market-list.json'       // url data source
            }).init()
        },
        theme_init: function() {
            HomepageApp.theme_slideshow();
            HomepageApp.theme_testimoni();
            HomepageApp.theme_mobilenav();
            HomepageApp.theme_marketwidget();
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        HomepageApp.theme_init();
    });