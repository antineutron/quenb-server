var version = "Webclient,0,0,10";
var timeout = 30000;

// MAIN BODY STARTS HERE
$(document).ready(function(){

    // Build our dict of client info based on the URL and anything else we know.
    // We do this once on the initial page load. The backend server may change
    // our client facts based on rules later on.
    var client_facts = getClientFacts();

    try {

        // Attempt to update our display indefinitely, exceptions will cause a fresh page reload
        check_display(client_facts);

    } catch (e) {
        // We will flash an error message up, and then refresh the page
        // in 30 seconds.
        $('.special').addClass('hidden');
        $('.special#tvstatic').removeClass('hidden');

        notify('error', e);
    
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

    // Form the query string to get our instructions
    var query_string = "/display?";
    for (key in client_facts) {
        query_string = query_string + '&' + key + '=' + client_facts[key];
    };

    $.ajax({
        'type' : 'get',
        'url' : query_string,
        'success' : function(data_string) {
            data = JSON.parse(data_string);
            process(client_facts, data);
        },
        'error' : function() {
            data = {
                'error': "Failure to contact control server.",
                'special_show': 'tvstatic'
            };
            process(client_facts, data);
        },
        'complete' : function() {
            foo = 'completed';
        }
    });

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
function process(client_facts, data) {

    // Keep track of how many requests in a row we've made
    client_facts.calls = client_facts.calls + 1;
    

    // Display errors for a short time
    if (data.error) {
        notify('error', data.error);
    }

    // Display info messages for a short time
    if (data.info) {
        notify('info', data.info);
    }

    // Force a page refresh if we need to restart the client
    if (data.restart_client) {
        notify('alert', 'This webclient will reload shortly.');

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
        // Get our instructions from the backend server and process them
        check_display(client_facts);
    }, client_facts.timeout);
}

function notify(type, text) {
    if (type == 'error') {
        $('#notices').css('color', '#B94A48');
        $('#notices').css('border-color', '#EED3D7');
        $('#notices').css('background-color', '#F2DEDE');
    } else if (type == 'alert') {
        $('#notices').css('color', '#468847');
        $('#notices').css('border-color', '#D6E9C6');
        $('#notices').css('background-color', '#DFF0D8');
    } else {
        $('#notices').css('color', '#3A87AD');
        $('#notices').css('border-color', '#BCE8F1');
        $('#notices').css('background-color', '#D9EDF7');
    }
    $('#notices').html(text);
    $('#notices').removeClass('hidden');
    setTimeout(function(){
        $('#notices').html('');
        $('#notices').addClass('hidden');
    }, 4000);
}



