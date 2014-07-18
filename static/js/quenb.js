// This stuff is in the templated page.

//var server_supplied_cid = "{{client_id}}";
//var our_ip = "{{addr}}";
//
//var query = "{{query_variables}}";


var version = "Webclient,0,0,10";
var timeout = 20000;

// MAIN BODY STARTS HERE
$(document).ready(function(){


    // Build our dict of client info based on the URL and anything else we know.
    // We do this once on the initial page load. The backend server may change
    // our client facts based on rules later on.
    var client_facts = getClientFacts();

    try {

        // Attempt to update our display indefinitely, exceptions will cause a fresh page reload
        process(client_facts);

    } catch (e) {
        // We will flash an error message up, and then refresh the page
        // in 30 seconds.
        $('.special').addClass('hidden');
        $('.special#tvstatic').removeClass('hidden');
    
        noty({
            type: 'error',
            text: e,
            layout: 'topCenter'
        });
    
        // Refresh the page, with no caching, after our default timeout limit
        // NB we do not use the timeout from client_facts in case it's been set to
        // something far too long so the display stays broken!
        setTimeout(function() {
            location.reload(true);
        }, timeout);
    }

});

// Does an AJAX request to the backend to request further instructions.
// Checks that we got valid data, and falls back to a static image
// if the attempt fails. 
function check_display(client_facts) {
    var data = {};

    // Form the query string to get our instructions
    var query_string = "/display?";
    for (key in client_facts) {
        query_string = query_string + '&' + key + '=' + client_facts[key];
    };

    $.ajax(query_string, {
        'async': false,
        'success' : function(data_string) {
            data = JSON.parse(data_string);
        },
        'error' : function() {
            data = {
                'error': "Failure to contact control server.",
                'special_show': 'tvstatic'
            };
        }
    });

    return data;
}

// Given two hashes, return a merged hash
function overrideFacts(facts1, facts2){
    if (typeof facts2 !== 'object' || facts2 == null){
        return facts1;
    }
    return $.extend(facts1, facts2);
}

// Parses the request URI to extract client-supplied details
// and adds in other known facts e.g. API version, screen width,
// number of calls so far etc.
function getClientFacts(){

    // Remove leading ? and split on & to get key=value pairs
    var qstring_params = window.location.search.substr(1).split('&');

    // Set defaults...
    var client_facts = {
        "version"       : version,
        "last_query"    : window.location.href,
        "window_width"  : $(document).width(),
        "window_height" : $(document).height(),
        "calls"         : 0,
        "timeout"       : timeout,
    };

    // Override with anything specified in the query string
    // NB this may be new data e.g. MAC address, or it may
    // override e.g. the window width for fun (or debugging).
    client_facts = overrideFacts(client_facts, qstring_params);

    return client_facts;
}

// Called repeatedly, this is the "real" start point.
function process(client_facts) {

    // Keep track of how many requests in a row we've made
    client_facts.calls = client_facts.calls + 1;
    
    // Get our instructions from the backend server
    var data = check_display(client_facts);

    // Display errors for a short time
    if (data.error) {
        var notification = noty({
                type: 'error',
                text: data.error,
                timeout: 5000,
                layout: 'topCenter'
            });
    }

    // Display info messages for a short time
    if (data.info) {
        var notification = noty({
                type: 'info',
                text: data.info,
                timeout: 5000,
                layout: 'topCenter'
            });
    }

    // Force a page refresh if we need to restart the client
    if (data.restart_client) {
        noty({
            type: 'alert',
            text: "This webclient will reload shortly.",
            layout: 'topCenter'
        });

        // Reload in 5 seconds.
        setTimeout(function() {
            location.reload(true);
        }, 5000);
    }

    // Hide the special things and full screen image
    $('.special').addClass('hidden');
    $('#imgfullscreen').addClass('hidden');

    // Show special items by un-hiding them
    if (data.special_show) {
        $('.special#' + data.special_show).removeClass('hidden');

    // Show fullscreen image by loading in the image source and un-hiding it
    } else if (data.display_image && !data.display_url){
        $('#imgfullscreen').attr('src', data.display_image);
        $('#imgfullscreen').removeClass('hidden');
    }


    var sent_display_url = data.display_url;
    var force_refresh = data.force_refresh;
    var last_display_url = client_facts.last_displayed;

    // Make sure we have an iframe for content to live in...
    if (!$('iframe').length) {
        $('body').append('<iframe>');
    }

    if ((sent_display_url !== last_display_url) || force_refresh) {
        $('iframe').attr('src', sent_display_url);
    }

    client_facts.last_displayed = data.display_url;
    client_facts.last_data = data;

    // If given any client facts to overwrite, overwrite them...
    if (data.client_facts) {
        client_facts = overrideFacts(client_facts, data.client_facts);
    }

    // Call ourselves again, when we're done
    setTimeout(function() {
        process(client_facts);
    }, client_facts.timeout);
}




