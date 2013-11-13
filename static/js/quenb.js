// This stuff is in the templated page.

//var server_supplied_cid = "{{client_id}}";
//var our_ip = "{{addr}}";
//
//var query = "{{query_variables}}";

// TODO First, check whether there's a cookie set for the client id, if so
// use that. Otherwise, use the random one the page just generated.

var version = "Webclient,0,0,8";

if ("cid" in client_query) {
    var cid = client_query.cid;
} else {
    var cid = server_supplied_cid;
}

if ("addr" in client_query) {
    var addr = client_query.addr;
} else {
    var addr = our_ip;
}

// TODO Get location from user
function check_display(query_string, next_step, internal_data) {
    $.get(query_string, function(data_string) {
        var data = JSON.parse(data_string);
        next_step(data, internal_data);

    })
    .fail(function() {
        var fake_data = {
            'error': "Failure to contact control server.",
            'special_show': 'tvstatic'
        };

        next_step(fake_data, internal_data);
    });
}

function looplet(internal_data) {
    var cq = internal_data.client_query;

    internal_data.calls = internal_data.calls + 1;

    var variables = {
        "cid": internal_data.cid,
        "version": internal_data.version,
        "addr": internal_data.addr,
        "calls": internal_data.calls,
    }
    if (internal_data.token) {
        variables.token = internal_data.token;
    }


    // Queries supplied when the client was started ALWAYS override what the client
    // would otherwise do. This is becuase most variables supplied to the webclient
    // are either static information (like mac) or just used for debugging (like cid)

    for (key in internal_data.client_query) {
        variables[key] = internal_data.client_query[key];

    };

    var query_string = "/display";
    var first = true;

    for (key in variables) {
        var sep = first ? "?" : "&";
        first = false;

        query_string = query_string + sep + key + '=' + variables[key];
    };

    internal_data.last_query = query_string;

    check_display(query_string, looplet2, internal_data);
}

function looplet2(data, internal_data) {
    if (data.error) {
        var notification = noty({
                type: 'error',
                text: data.error,
                timeout: 5000,
                layout: 'topCenter'
            });
    }
    if (data.info) {
        var notification = noty({
                type: 'info',
                text: data.info,
                timeout: 5000,
                layout: 'topCenter'
            });
    }

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

    $('.special').addClass('hidden');
    $('#imgfullscreen').addClass('hidden');

    if (data.special_show) {
        $('.special#' + data.special_show).removeClass('hidden');
    } else if (data.display_image){
        $('#imgfullscreen').attr('src', data.display_image);
        $('#imgfullscreen').removeClass('hidden');
    }


    var sent_display_url = data.display_url;
    var force_refresh = data.force_refresh;
    var last_display_url = internal_data.last_displayed;

    if (!$('iframe').length) {
        $('body').append('<iframe>');
    }

    if ((sent_display_url !== last_display_url) || force_refresh) {
        $('iframe').attr('src', sent_display_url);
    }

    internal_data.last_displayed = data.display_url;
    internal_data.last_data = data;

    // If given a token, store it and send it back
    if (data.token) {
        internal_data.token = data.token;
    }

    if (data.sleep_time) {
        var sleep_time = data.sleep_time;
    } else {
        // Sleep for 10 seconds, for default.
        var sleep_time = 10000;

    }

    if (data.set_clientid) {
        internal_data.cid = data.set_clientid;
    }

    // Call ourselves again, when we're done
    setTimeout(function() {
        looplet(internal_data);
    }, sleep_time);
}

try {
// MAIN BODY STARTS HERE
    var internal_data = {
        'calls': 0,
        'addr': addr,
        'cid': cid,
        'version': version,
        'client_query': client_query,
    };
    looplet(internal_data);
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

    // In 30 seconds, refresh (without the cache) the page.
    setTimeout(function() {
        location.reload(true);
    }, 30000);
}

