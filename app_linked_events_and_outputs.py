import dash
import dash_html_components as html
import dash_core_components as dcc

from dash.dependencies import Input, Output, Current, Source

app = dash.Dash()


app.layout = html.Div([
    dcc.Input(
        placeholder='What needs to be done?',

        # Here I use a proposed app.trigger, replacing the use of 
        # 'Event()' on the callback, making it easier to find out
        # what updates can be caused by a component
        # The 'submit' Event doesn't currently exist on dcc.Input
        #but it could be nice if it did
        submit=app.trigger(add_item)
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
            click=app.trigger(remove_selected_items),
            children=app.compute(display_clear_completed)
        )
    ])
])

def create_todo_item(todo_text, todo_number):
    #We declare each component separately so we can name the elements
    #without the need for an id, but it might be that we need one 
    #for other reasons such as simpler debugging
    #so could leave them in

    ItemSelected = dcc.CheckList(
                options=[{'label': '', 'value': 'selected'}],
                values=[],
                id='item-selected-{}'.format(todo_number),
                todo_number=todo_number
            )

    RemoveItem = html.Span(
                'Remove',
                click=app.trigger(remove_item),

                #Don't know if custom props are supported, but it would
                #make things a bit easier for linking related components
                todo_number=todo_number
            )

    return html.Div(
        #Leave this id in because it could be handy in any callback tree display
        #The children will be more obvious so don't need a name (assuming their type is shown)
        #It is also needed for some input selectors
        id='item-container-{}'.format(todo_number),
        style=app.compute(
                #Alternatively could use a 
                #single callback that generated the combined style
                todo_style_completed(ItemSelected),
                todo_style_filtered(ItemSelected)
            ),
        children=[
            ItemSelected,
            html.Span(todo_text),
            RemoveItem
        ],

        todo_number=todo_number
    )


# Add a todo to the end of the list
# Source() could allow us to get properties or meta-data directly
# from the triggering component. 
# It is another special case of State(), like Current() is
@app.callback(state=[Source('value'), Current()])
def add_item(todo_text, existing_todos):
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
def todo_style_completed(ItemSelected):
    
    #Fetch the id out, but might be handy if Input() could
    #take a component and fetch the id itself
    itemSelectedId = ItemSelected.id

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
def todo_style_filtered(ItemSelected):

    itemSelectedId = ItemSelected.id

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
            Input(itemSelectedId, 'value')
        ],
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


# Remove a todo item, which now just needs to know the 
# which specific item got clicked
@app.callback(state=[Source("todo_number"), Current()])
def remove_item(todo_number, existing_todos):
    # It might be inefficient to bring in the full children tree
    # but at least the calls can be chained together so that they are only
    # brought back once for a given change and then passed through each 
    # function in python
    return [todo for todo in existing_todos if todo.todo_number != todo_number]

@app.callback(state=[
                State('item-selected-{*n:d}', 'values'), 
                Current()
               ])
def remove_selected_items(item_values, item_numerical_ids, existing_todos):   
    #We don't need the ids in this case
    filtered_items = []

    for (todo, selected_values) in zip(existing_todos, item_values):
        if 'selected' not in selected_values:
            filtered_items.append(todo)
    
    return filtered_items