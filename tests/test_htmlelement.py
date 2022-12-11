from ..htmlelement import HTMLElement 

def test_htmlElement_render(): 
    htmlElement = HTMLElement(
        class_name="something", 
        text="some_text", 
        style="body{};", 
        childrens=[],
    )
    rendered = htmlElement.render()
    assert '<div class=something elemId=0 >some_text</div>\n' in rendered
    assert "async function postData(url = '', data = {})" in rendered 
    assert 'function getCurrentURL ()' in rendered


def test_htmlElementNested_render(): 
    htmlElement = HTMLElement(
        class_name="something", 
        text="some_text", 
        style="body{};", 
        childrens=[
            HTMLElement(
                class_name="something_2", 
                text="some_text", 
                style="body{};", 
                childrens=[],
            )
        ],
    )

    rendered = htmlElement.render()
    assert (
            '<div class=something elemId=0 >some_text<div class=something_2 elemId=0-0 >some_text</div></div>\n'
        ) in rendered


def test_htmlElementNested_renderV2(): 
    htmlElement = HTMLElement(
        class_name="something", 
        text="some_text", 
        style="body{};", 
        childrens=[
            HTMLElement(
                class_name="something_2", 
                text="some_text", 
                style="body{};", 
                childrens=[],
            )
        ],
    )

    result = htmlElement.renderV2()
    state = result["state"]
    assert not state["_changed"] 
    assert not result["changes"]

    htmlElement.text = ""
    result = htmlElement.renderV2()
    state = result["state"]
    assert state["_changed"] 

    # as the first element have changed, we should have it in the changes 
    print(result["changes"]["something"])
    assert result["changes"]["something"] == (
            '<div class=something elemId=0 ><div class=something_2 elemId=0-0 >some_text</div></div>'
    ) 


