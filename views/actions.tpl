 %include head.tpl current_user=current_user
<div class="modal fade modal-dialog modal-content" id="addActionModal" tabindex="-1" role="dialog" aria-labelledby="addActionModalLabel" aria-hidden="true">
  <div class="modal-header">
  <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
  <h4 id="addActionModalLabel">Add action</h4>
  </div>

  <form class="well" data-target="#addActionModal" action="/admin/action" method="PUT" id="addActionModalForm">
  <div class="modal-body">
      <fieldset>
        <label for='title'>Title</label>
        <input type='text' name='title' placeholder='Title'/>
        <label for='description'>Description</label>
        <input type='text' name='description' placeholder='Description'/>
        <label for='plugin'>Plugin function</label>
        <select name='plugin'>
          % for plugin in plugins:
          <option value='{{plugin}}'>{{plugin}}</option>
          % end for
        </select>
        <label for='args'>Plugin function arguments (comma-separated)</label>
        <input type='text' name='args'/>
      </fieldset>
  </div>

  <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
    <input type="submit" class="btn btn-primary" id="addActionModalSubmit" value="Add new action"/>
  </div>
  </form>
</div>
    <div class="center">
      <h2>Actions</h2>
      <p>
	    When a client matches a rule, an action is performed - usually displaying a page or an image.
      </p>

	  <button class="btn btn-primary btn-sm" data-toggle="modal" data-target="#addActionModal">
	    Add a new action
	  </button>

      <table id='actionTable'>
	    <thead>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th><th>Delete</th></tr>
		</thead>
		<tbody>
        % for action in actions:
        <tr id='action-{{action['id']}}'>
          <td>
			<span class='editable'>{{action['title']}}</span></td>
          <td>
		    <span class='select_plugin' style="display: inline">{{action['module']}}.{{action['function']}}</span>
			(<span class='module_args'>{{action['args'] or ''}}</span>)
	      </td>
          <td><span class='editable'>{{action['description']}}</span></td>
		  <td>
		    % if action['id'] > 0:
		    <button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'
			        onclick='deleteAction({{action['id']}}); return false;'></button>
			% end if
		  </td>
        </tr>
        % end for
		</tbody>
	    <tfoot>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th><th>Delete</th></tr>
		</tfoot>
      </table>

 







      <script>
	  // When add action modal form is submitted, convert to
	  // an AJAX request and update the table with returned data (or show error)
      $('form#addActionModalForm').on('submit', function(event) {
        var $form = $(this);
		var $target = $form.attr('data-target');
		var oData = $('#actionTable').dataTable();
 
        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),
 
            success: function(data, status) {
				d = data['action'];
			    buttonText = "<button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'\n"+
                             "       onclick='deleteAction(" + d['id'] + "); return false;'></button>";
				tblRow = [d['title'], d['module']+'.'+d['function']+'('+d['args']+')', d['description'], buttonText];
				oData.fnAddData(tblRow);
				$($target).modal('hide');
            },
			error : function(data){
				$($target).modal('hide');
				noty({
                  type: 'error',
                  text: 'Failed to create action: '+data.statusText,
                  timeout: 5000,
                  layout: 'topCenter'
                });
			}
        });
 
        event.preventDefault();

      });


	  // When the delete button is pushed, ask for confirmation then ajax-delete the action
	  function deleteAction(id){
		var oData = $('#actionTable').dataTable();
		$.ajax({
			'url' : '/admin/action/'+id,
			'type' : 'DELETE',
			'dataType' : 'json',
			'success' : function(data){
				oData.fnDeleteRow($('tr#action-'+id)[0]);
			},
			'error' : function(data){
				noty({
                  type: 'error',
                  text: 'Failed to delete action: '+data.statusText,
                  timeout: 5000,
                  layout: 'topCenter'
                });
			}
		});
	  }


		// Set up theDataTable layout with inline edit support
		$(document).ready(function() {
    		var oTable = $('#actionTable').dataTable();

            // Submit function for inline editing 
            var inline_submit = function ( value, settings ) { 
                actionID = this.parentNode.getAttribute('id'); 
                fieldPosition = oTable.fnGetPosition( this )[2]; 
                fieldName = $('#actionTable thead th')[fieldPosition].innerHTML.toLowerCase(); 
                return { 
                    "action_id": actionID, 
                    "field":  fieldName 
                }; 
            }; 

     
            // Callback function for inline editing 
            var inline_update = function( sValue, y ) { 
                var aPos = oTable.fnGetPosition( this ); 
                oTable.fnUpdate( sValue, aPos[0], aPos[1] ); 
            }; 
 
            // Make text fields in-place editable 
            oTable.$('td.editable').editable( '/admin/actions/', { 
                "type" : 'text', 
                "callback": inline_update, 
                "submitdata": inline_submit, 
                "width": "100%", 
                "onblur" : "submit" 
            } ); 

            oTable.$('.module_args').editable( '/admin/actions/', { 
                "type" : 'text', 
                "callback": inline_update, 
                "submitdata": function(value, settings){
					return {
						"action_id": this.parentNode.getAttribute('id'),
						"args" : value
					};
				},
                "width": "100%", 
                "onblur" : "submit" 
            } ); 
 
            // Make selectable fields select lists 
            oTable.$('span.select_plugin').editable( '/admin/actions/update_field', { 
                "type" : "select",
                "loadurl" : "/admin/api/plugins",
                "callback": inline_update,
                "submitdata": function(value, settings){
					return {
						"action_id": this.parentNode.getAttribute('id'),
						"function_call" : value
					};
				},
                "width": "100%",
				"submit" : "OK",
            } );

		} );
      </script>

    </div>

% include tail.tpl
