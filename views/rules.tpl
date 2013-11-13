 % include head.tpl
    <div class="center">
      <h2>Rules</h2>
      <p>
        Rules are used to identify a client and get it to perform an action (such as displaying a page).
        This is the current list of rules in the database:
      </p>

      <table id='ruleTable'>
	    <thead>
          <tr><th>Priority</th><th>Rule</th><th>Action</th></tr>
		</thead>
		<tbody>
        % for rule in rules:
        <tr id='{{rule['id']}}'>
          <td class='spinner'>
            {{rule['priority']}}
          </td>
          <td class='editable'>{{rule['rule']}}</td>
          <td class='action_select'>
		    {{rule['title']}}
		  </td>
        </tr>
		</tbody>
        % end for
	    <tfoot>
          <tr><th>Priority</th><th>Rule</th><th>Action</th></tr>
		</tfoot>
      </table>

      <script>


        $(document).ready(function() {

			// Make a DataTable out of our rules list
			var oTable = $('#ruleTable').dataTable();

    		// Submit function for inline editing
    		var inline_submit = function ( value, settings ) {
    			ruleID = this.parentNode.getAttribute('id');
                fieldPosition = oTable.fnGetPosition( this )[2];
                fieldName = $('#ruleTable thead th')[fieldPosition].innerHTML.toLowerCase();
                return {
                    "rule_id": ruleID,
                    "field":  fieldName
                };
    		};
    
    		// Callback function for inline editing
    	    var inline_update = function( sValue, y ) {
    			var aPos = oTable.fnGetPosition( this );
    			oTable.fnUpdate( sValue, aPos[0], aPos[1] );
    		};

			// Make text fields in-place editable
            oTable.$('td.editable').editable( '/admin/rules/update_field', {
				"type" : 'textarea',
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );

			// Make integer fields spinners
            oTable.$('td.spinner').editable( '/admin/rules/update_field', {
				"type" : "text",
				//loadurl : "/admin/api/actions/",
				//"data" : {"first" : "First", "second": "Second"},
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );

			// Make selectable fields select lists
            oTable.$('td.action_select').editable( '/admin/rules/update_field', {
				"type" : "select",
				"loadurl" : "/admin/api/actions/",
				//"data" : {"1" : "First", "2": "Second"},
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );
        } );
      </script>


    </div>
% include tail.tpl
