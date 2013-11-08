// Dear lord, I'm building interfaces with javascript now

function make_basic_auth(user, password) {
    var tok = user + ':' + password;
    var hash = btoa(tok);
    return "Basic " + hash;
}

var state;

$(document).ready(function() {
    $('#loginform').submit(function(event) {
        event.preventDefault();
        $('input').prop('disabled', true);

        state = {
            'username': $('input[name="username"]').val(),
            'password': $('input[name="password"]').val()
        }
        state.auth_header = make_basic_auth(state.username, state.password);


        stage1(state);

        return false;
    });

    $('input').prop('disabled',false);
    $('#dialog-form').dialog({
        autoOpen: false,
    });
});

function stage1(state) {
    // Check whether the server is up.
    $.get("/api/ping")
    .done(function() {
        stage2(state);
    })
    .fail(function () {
        noty({
            type: 'error',
            text: 'Pinging the server failed. Try again later.',
            layout: 'topCenter',
            timeout: 10000
        });
        $('input').prop('disabled',false);
    });
}

function stage2(state) {
    // Check whether our login credentials are good.
    $.ajax({
        url: "/api/version",
        headers: {'Authorization': state.auth_header}
    })
    .done(function() {
        stage3(state);
    })
    .fail(function() {
        noty({
            type: 'alert',
            text: 'Bad login credentials. Please try again.',
            layout: 'topCenter',
            timeout: 10000
        });
        $('input').prop('disabled',false);
        $('input[name="password"]').val('');
    });
}

function stage3(state) {
    $('form#loginform').fadeOut();
    $.ajax({
        url: "/api/rules",
        headers: {'Authorization': state.auth_header}
    })
    .done(function(str) {
        state.rules = JSON.parse(str);
        stage4(state);
    })
    .fail(function() {
        noty({ text: 'Rules get failed. WTF.' });
    })
};

function stage4(state) {
    $.ajax({
        url: "/api/outcomes",
        headers: {'Authorization': state.auth_header}
    })
    .done(function(str) {
        state.outcomes = JSON.parse(str);
        stage4andabit(state);
    })
    .fail(function() {
        noty({ text: 'Outcomes get failed. WTF.' });
    })
};

function stage4andabit(state) {
    $.ajax({
        url: "/api/code",
        headers: {'Authorization': state.auth_header}
    })
    .done(function(str) {
        state.code = JSON.parse(str);
        stage5(state);
    })
    .fail(function() {
        noty({ text: 'Code get failed. WTF.' });
    })
};

function stage5(state) {
    $('div#items').empty();
    $('#refresh')
    .removeClass('hidden')
    .click(function() {
        stage3(state);
        $(this).addClass('hidden');
    });

    // Finally we have most of the stuff. Let's tabulate and display.
    var element_id = 0;
    for (type in {'rules': 'rules', 'outcomes': 'outcomes', 'code':'code'}) {
        var items = state[type];
        $('div#items').append('<div id="' + type + '"></div>');
        $('div#' + type)
            .append('<h1>' + type + '</h1>')
            .append('<table id="' + type + '"></table>');
        var template_item = items[0];

        $('table#' + type).append('<tr id="' + type + '"></tr>');
        for (field in template_item) {
            $('tr#' + type).append('<td class="header">' + field + '</td>');
        }

        for (i in items) {
            var item = items[i];
            $('table#' + type).append('<tr id="' + type + item.id + '"></tr>');
            for (field in item) {

                var onclick = function() {
                    var type = $(this).data('type');
                    var item = $(this).data('item');

                    item_popup(item, "edit",
                            function(item) {
                                put_item(state, type, 'edit', item);
                            },
                            function(item) {
                                delete_item(state, type, item.id);
                            });
                };

                var tr = $('tr#' + type + item.id);
                if (field == 'body') {
                    tr.append('<td id="' + element_id + '" ><pre>' + item[field] + '</pre></td>');
                } else {
                    tr.append('<td id="' + element_id + '" >' + item[field] + '</td>');
                }
                tr.data('item', item)
                .data('type', type)
                .click(onclick);

                $('td#' + element_id)
                .data('item', item)
                .data('type', type)
                .click(onclick);

                element_id = element_id + 1;

            }
            $('tr#' + type + item.id)
                .append('<td id="delete-' + type + item.id + '" class="delete-item">X</td>');
            $('td#delete-' + type + item.id)
            .data('type',type)
            .data('id',item.id)
            .click(function() {
                var type = $(this).data('type');
                var id = $(this).data('id');
                delete_item(state, type, id);
                return false;
            });
        }
        $('table#' + type).append('<tr id="new-' + type + '"></tr>');
        $('tr#new-' + type)
            .append('<td id="new-' + type + '" class="new-item fake-link">Create new item</td>')
        $('#new-' + type)
        .data('type',type)
        .data('template', template_item)
        .click(function() {
            var type = $(this).data('type');
            var template = $(this).data('template');
            item_popup(template, 'new',
                function(edited_item) {
                    put_item(state, type, 'new', edited_item);
                });
        });
    }
}

function item_popup(item, edit_or_new, callback, delete_callback) {
    $('#dialog-fieldset').empty();

    for (field in item) {
        if (field == 'id')
            continue;
        if (edit_or_new == 'edit') {
            var value = item[field];
        } else if (edit_or_new == 'new') {
            var value = '';
        } else {
            // FIXME Invalid input, complain about something
            throw "Invalid edit_or_new input";
        }

        $('#dialog-fieldset')
            .append('<label for="' + field + '">' + field + '</label><br>');
        if (field == 'body') {
            $('#dialog-fieldset')
                .append('<textarea name="' + field + '" id="' + field + '" class="text ui-widget-content ui-corner-all popup-input"/><br>')

        } else {
            $('#dialog-fieldset')
                .append('<input type="text" name="' + field + '" id="' + field + '" class="text ui-widget-content ui-corner-all popup-input"/><br>');
        }

        $('.popup-input#' + field).val(value);
    }

    var buttons = {
            "Submit": function() {
                var values = {};
                $('.popup-input').each(function(index) {
                    values[$(this).attr('name')] = $(this).val();
                    if (edit_or_new == 'edit') {
                        values['id'] = item.id;
                    };
                });
                $(this).dialog("close");
                callback(values);
            },
            "Cancel": function() {
                $(this).dialog("close");
            }
    }
    if (edit_or_new == 'edit') {
        buttons['Delete'] = function() {
            delete_callback(item);
            $(this).dialog("close");
        }
    }
    $('#dialog-form').dialog({
        autoOpen: false,
        modal: true,
        buttons: buttons,
        title: edit_or_new + ' item',
    });
    $('#dialog-form').dialog("open");
}

function put_item(state, type, edit_or_new, item) {
    var url = '/api/' + type;
    if (edit_or_new == 'edit') {
        url = url + '/' + item.id;
    }
    if (edit_or_new == 'new') {
        delete item['id'];
    }

    $.ajax({
        url: url,
        headers: {'Authorization': state.auth_header},
        type: 'PUT',
        data: item,
    })
    .done(function(str) {
        noty({ type: 'success', timeout: 10000,
            text: edit_or_new + ' success'});
        stage3(state);
    })
    .fail(function() {
        noty({ type: 'error', text: edit_or_new + ' failed', timeout: 10000 });
    });
}

function delete_item(state, type, id) {
    $.ajax({
        url: '/api/' + type + '/' + id,
        headers: {'Authorization': state.auth_header},
        type: 'DELETE',
    })
    .done(function(str) {
        noty({ text: '' + type + ' ' + id + ' deleted', type: 'success',
            timeout: 10000});
        stage3(state);
    }).fail(function() {
        noty({type: 'error', text: 'delete failed', timeout: 10000});
    });
}
