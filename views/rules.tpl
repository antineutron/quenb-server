 % include head.tpl current_user=current_user
    <div class="center">
      <h2>Rules</h2>
      <p>
        Rules are used to identify a client and get it to perform an action (such as displaying a page).
        This is the current list of rules in the database:
      </p>

	  <button class="btn btn-primary btn-sm" data-toggle="modal" data-target="#addRuleModal">
	    Add a new rule
	  </button>

      <table id='ruleTable'>
	    <thead>
          <tr><th>Priority</th><th>Rule</th><th>Action</th></tr>
		</thead>
		<tbody>
        % for rule in rules:
        <tr id='{{rule['id']}}'>
		  <td>
		    % if rule['id'] > 0:
		    <button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'
			        onclick='deleteRule({{rule['id']}}); return false;'></button>
			% end if
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

<div class="modal fade modal-dialog modal-content" id="addRuleModal" tabindex="-1" role="dialog" aria-labelledby="addRuleModalLabel" aria-hidden="true">
  <div class="modal-header">
  <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
  <h4 id="addRuleModalLabel">Add rule</h4>
  </div>

  <form class="well" data-target="#addRuleModal" action="/admin/rule" method="PUT" id="addRuleModalForm">
  <div class="modal-body">
      <fieldset>
        <label for='rule'>Rule</label>
        <input type='textarea' name='rule' value='true'/>

        <label for='action'>Action to take when rule 'hits'</label>
        <select name='action'>
          % for action in actions:
          <option value='{{action['id']}}'>{{action['title']}} ({{action['description']}})</option>
          % end for
        </select>
        <label for='priority'>Rule priority (if multiple rules match, higher priority overrides lower priority)</label>
		<input type='text' name='priority' value='1'/>
      </fieldset>
  </div>

  <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
    <input type="submit" class="btn btn-primary" id="addRuleModalSubmit" value="Add new rule"/>
  </div>
  </form>
</div>
      <script>

	  // When add rule modal form is submitted, convert to
	  // an AJAX request and update the table with returned data (or show error)
      $('form#addRuleModalForm').on('submit', function(event) {
        var $form = $(this);
		var $target = $form.attr('data-target');
		var oData = $('#ruleTable').dataTable();
 
        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),
 
            success: function(data, status) {
				d = data['rule'];
				tblRow = [d['priority'], d['rule']+'.'+d['action_title']];
				oData.fnAddData(tblRow);
				$($target).modal('hide');
            },
			error : function(data){
				$($target).modal('hide');
				noty({
                  type: 'error',
                  text: 'Failed to create rule: '+data.statusText,
                  timeout: 5000,
                  layout: 'topCenter'
                });
			}
        });
 
        event.preventDefault();

      });


	  // When the delete button is pushed, ask for confirmation then ajax-delete the rule
	  function deleteRule(id){
		var oData = $('#ruleTable').dataTable();
		$.ajax({
			'url' : '/admin/rule/'+id,
			'type' : 'DELETE',
			'dataType' : 'json',
			'success' : function(data){
				oData.fnDeleteRow($('tr #'+id));
			},
			'error' : function(data){
				noty({
                  type: 'error',
                  text: 'Failed to delete rule: '+data.statusText,
                  timeout: 5000,
                  layout: 'topCenter'
                });
			}
		});
	  }




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
            oTable.$('td.editable').editable( '/admin/actions/update_field', {
				"type" : 'textarea',
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );

			// Make integer fields spinners
            oTable.$('td.spinner').editable( '/admin/actions/update_field', {
				"type" : "text",
				//loadurl : "/admin/api/actions/",
				//"data" : {"first" : "First", "second": "Second"},
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );

			// Make selectable fields select lists
            oTable.$('td.action_select').editable( '/admin/actions/update_field', {
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
