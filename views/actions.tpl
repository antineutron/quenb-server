 %include head.tpl current_user=current_user
    <div class="center">
      <h2>Actions</h2>
      <p>
	    When a client matches a rule, an action is performed - usually displaying a page or an image.
      </p>

      <table id='actionTable'>
	    <a href='#' onclick='addAction(); return false;'>Add new action</a>
	    <thead>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th></tr>
		</thead>
		<tbody>
        % for action in actions:
        <tr id='{{action['id']}}'>
          <td>
		    % if action['id'] > 0:
		    <button class='btn btn-default glyphicon glyphicon-remove-circle' alt='Delete'
			        onclick='deleteAction({{action['id']}}); return false;'></button>
			% end if
			<span class='editable'>{{action['title']}}</span></td>

          <td>
		    <span class='select_plugin' style="display: inline">{{action['module']}}.{{action['function']}}</span>
			(<span class='module_args'>{{action['args'] or ''}}</span>)
	      </td>
          <td><span class='editable'>{{action['description']}}</span></td>
        </tr>
        % end for
		</tbody>
	    <tfoot>
          <tr><th>Title</th><th>Plugin function call</th><th>Description</th></tr>
		</tfoot>
      </table>

      <script>
	  function addAction(){
		var oData = $('#actionTable').dataTable();
		$.ajax({
			'url' : '/admin/action',
			'type' : 'PUT',
			'data' : {'title' : '', 'description' : '', 'plugin' : '', 'args' : ''},
			'dataType' : 'json',
			'success' : function(data){
				d = data['action'];
				tblRow = [d['title'], d['module']+'.'+d['function']+'('+d['args']+')', d['description']];
				oData.fnAddData(tblRow);
			},
			'error' : function(data){
				noty({
                  type: 'error',
                  text: 'Failed to create action: '+data.statusText,
                  timeout: 5000,
                  layout: 'topCenter'
                });
			}
		});
	  }

	  function updateAction(id, data){
		var oData = $('#actionTable').dataTable();
		$.ajax({
			'url' : '/admin/action/'+id,
			'type' : 'POST',
			'data' : data,
			'dataType' : 'json'
		});
	  }

	  function deleteAction(id){
		var oData = $('#actionTable').dataTable();
		$.ajax({
			'url' : '/admin/action/'+id,
			'type' : 'DELETE',
			'dataType' : 'json',
			'success' : function(data){
				oData.fnDeleteRow($('tr #'+id));
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
