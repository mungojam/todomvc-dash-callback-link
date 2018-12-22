import dash
import dash_html_components as html
import dash_core_components as dcc

from dash.dependencies import Input, Output, Current

app = dash.Dash()


app.layout = html.Div([
    dcc.Input(
        placeholder='What needs to be done?',
        id='add-todo'
    ),

    html.Div(
        id='todo-container', 
        children=app.compute(
                    add_item, 
                    remove_item, 
                    remove_selected_items, 
                    default=[]
                )
    ),

    html.Div([
        html.Span(
            id='counter', 
            children=app.compute(num_items_completed)
        ),
        html.RadioItems(
            id='todo-filter',
            options=[
                {'label': i, 'value': i} for i in [
                    'All', 'Active', 'Completed'
                ]
            ],
            value='All'
        ),
        html.Span(
            id='clear-completed',
            children=app.compute(display_clear_completed)
        )
    ])
])

def create_todo_item(todo_text, todo_number):
    itemSelectedId = 'item-selected-{}'.format(todo_number)

    return html.Div(
        id='item-container-{}'.format(todo_number),
        style=app.compute(
                #Alternatively could use a 
                #single callback that generated the combined style
                todo_style_completed(itemSelectedId),
                todo_style_filtered(itemSelectedId)
            ),
        children=[
            dcc.CheckList(
                options=[{'label': '', 'value': 'selected'}],
                values=[],
                id=itemSelectedId
            ),
            html.Span(todo_text),
            html.Span(
                'Remove',
                id='item-remove-{}'.format(todo_number)
            )
        ]
    )


# Add a todo to the end of the list
@app.callback([Input('add-todo', 'n_enter_timestamp')],  
              [State('add-todo', 'value'),
               Current()])
def add_item(n_enter_timestamp, todo_text, existing_todos):
    #We can have a go at fixing the identified bug with the 
    #original solution by finding the maximum id (not implemented here)
    max_id = find_max_todo_id(existing_todos)

    existing_todos.append(create_todo_item(
        todo_text, 
        #still with the identified bug if any todos in the 
        #middle have been deleted
        max_id + 1
    ))

    return existing_todos


# Strike-out the todo text when the item is selected
def todo_style_completed(itemSelectedId):
    
    #This could alternatively be declared right alongside the component
    #when being built. I may explore that in the next version
    @app.callback([Input(itemSelectedId, 'value')])
    def inner(value):
        if 'selected' in value:
            return {
                'text-decoration': 'line-through',
                'color': 'grey'
            }
        else:
            return {}
    
    return inner

# Hide/show items depending on the toggle buttons on the bottom
def todo_style_filtered(itemSelectedId):

    #This callback takes 'Current' which is the current 
    #value of the output, allowing Outputs to be created by 
    #chaining multiple callbacks together. I am including it 
    #in the State array. It's a similar idea to redux reducers

    #Note that the original example had item-selected as State
    #which would mean that newly marked completed items
    #wouldn't disappear if filter is 'Active'
    #In this implementation, we can have identical inputs triggering
    #the same outputs because we define the order on the component
    #(or in another function that it calls if we want to 
    #keep the ordering logic out of the layout)
    @app.callback(
        [
            Input('todo-filter', 'value'),
            Input(itemSelectedId, 'value')],
            [Current()]
        )
    def inner(todo_filter, value, currentStyle):
        if todo_filter == 'All':
            visible = True
        elif todo_filter == 'Active':
            visible = 'selected' in value
        else:
            visible = not 'selected' in value

        if visible:
            return {**currentStyle, 'display': 'block'}
        else:
            return {**currentStyle, 'display': 'none'}

    return inner


# Update the counter at the bottom of the page
@app.callback([Input('item-selected-{*n:d}', 'value')])
def num_items_completed(values, item_numerical_ids):
    # values for a single checklist is an array
    # in this case, [] or ['selected'].
    # since there are multiple inputs, this would be an array of arrays?
    # e.g. `[ [], ['selected'], [], [], ['selected'] ]`
    return '{} items completed'.format(len([
        item for item in values if item == 'selected'
    ]))


# Display "Clear completed" if there are completed tasks
@app.callback([Input('item-selected-{*n:d}', 'value')])
def display_clear_completed(values, item_numerical_ids):
    if len([item for item in values if item == 'selected']):
        return 'Clear completed'
    else:
        return None


# Remove a todo item
@app.callback([Input('item-remove-{n:d}', 'n_clicks')],[Current()])
def remove_item(n_clicks, id, existing_todos):
    # It might be inefficient to bring in the full children tree
    # but at least the calls can be chained together so that they are only
    # brought back once for a given change and then passed through each 
    # function in python
    return [todo for todo in existing_todos if todo.id != 'item-container-{}'.format(id)]

@app.callback([Input('clear-todos', 'n_clicks')],
              [
                State('item-selected-{*n:d}', 'values'), 
                Current()
               ])
def remove_selected_items(n_clicks, item_values, item_numerical_ids, existing_todos):   
    #We don't need the ids in this case
    filtered_items = []

    for (todo, selected_values) in zip(existing_todos, item_values):
        if 'selected' not in selected_values:
            filtered_items.append(todo)
    
    return filtered_items