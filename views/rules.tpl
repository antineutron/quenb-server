 % include head.tpl current_user=current_user
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
          <tr><th>Priority</th><th>Rule</th><th>Action</th><th>Delete</th></tr>
		</thead>
		<tbody>
        % for rule in rules['main']:
        <tr id='rule-{{rule['id']}}'>
		  <td>
		    <span class='editable_priority'>{{rule['priority']}}</span>
		  </td>
          <td>
            <span class='editable_rule'>{{rule['rule']}}</span>
		  </td>
          <td>
  		    <span class='editable_action'>{{rule['title']}}</span>
		  </td>
		  <td>
		    % if rule['id'] > 0:
		    <button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'
			        onclick='deleteRule({{rule['id']}}); return false;'></button>
			% end if
		  </td>
        </tr>
        % end for
		</tbody>
	    <tfoot>
          <tr><th>Priority</th><th>Rule</th><th>Action</th><th>Delete</th></tr>
		</tfoot>
      </table>

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
				$($target).modal('hide');
				d = data['rule'];
				buttonText = "<button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'\n"+
				             "       onclick='deleteRule(" + d['id'] + "); return false;'></button>";
				tblRow = [d['priority'].toString(), d['rule'], d['action_title'], buttonText];
				oData.fnAddData(tblRow);
            },
			error : function(data){
				$($target).modal('hide');
                alert('Failed to create rule: '+data.statusText);
			}
        });
 
        event.preventDefault();

      });


	  // When the delete button is pushed, ask for confirmation then ajax-delete the rule
	  function deleteRule(id){
		var oData = $('#ruleTable').dataTable();
		$.ajax({
			url : '/admin/rule/'+id,
			type : 'DELETE',
			dataType : 'json',
			success : function(data){
				oData.fnDeleteRow($('tr#rule-'+id)[0]);
			},
			error : function(data){
                alert('Failed to delete rule: '+data.statusText);
			}
		});
	  }




        $(document).ready(function() {

			// Make a DataTable out of our rules list
			var oTable = $('#ruleTable').dataTable({
				pageLength: 50
			});

    		// Submit function for inline editing
    		var inline_submit = function ( value, settings ) {
    			ruleID = this.parentNode.parentNode.getAttribute('id');
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
            oTable.$('.editable_priority').editable( function(value, settings){
				ruleID = this.parentNode.parentNode.getAttribute('id');
				$.ajax({
					url  : '/admin/rule/'+ruleID,
					type : 'POST',
	//				contentType: 'application/json; charset=UTF-8',
					dataType: 'json',
					data : {priority: value},
					success: function(){
						alert("Updated OK");
					},
					fail: function(){
						alert("Failed :-(");
					}
				});
            } );
            /*oTable.$('td.editable_priority').editable( '/admin/action/', {
				"type" : 'textarea',
                "callback": inline_update,
                "submitdata": inline_submit,
                "width": "100%",
				"onblur" : "submit"
            } );*/

        } );
      </script>


    </div>
% include tail.tpl
