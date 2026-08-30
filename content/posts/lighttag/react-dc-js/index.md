+++
title = "Using dc.js and Crossfilter With React"
date = 2019-02-10T00:00:00Z
draft = false
description = "A clean React pattern for integrating dc.js and Crossfilter to build interactive, high-dimensional charts."

[social]
image = "social.webp"
image_alt = "Archive cover for Using dc.js and Crossfilter With React."

[share]
disable = false
languages = ["en"]

[original_publication]
site = "LightTag.io"
path = "/blog/react-dc-js/"
+++
We're a natural language processing company and we usually blog about natural language processing. Today we're switching gears and writing a little about front end development, particularly about how to work with [dc.js](https://dc-js.github.io/dc.js/) in React.

If you are not familiar with DC.JS, it's a library that facilitates visual interaction with high dimensional data - you can click on one chart and all of the other charts change.
![What It Looks Like](example.webp)

Visually interacting with data is a great way to discover what's happening in it fast. At LightTag, our customers want to track the evolution and quality of their datasets and NLP models across multiple dimensions (Annotator, an annotation type, time, inter-annotator agreement etc). We've provided basic reports and API access to data to support this, however, we want to provide an easier more powerful mechanism for our customers to view their data. Ideally, we'd use DC.JS however it was not obvious how we could integrate it with the rest of our React App in a maintainable fashion. With the recent release of hooks we've taken another look and are happy to share a POC our team has put together.

The rest of this blog post described the POC we did, an implementation of the canonical dc example in React. You can try the [demo here](https://lighttag.github.io/dcjs-in-react/) and [clone the repo here](https://github.com/LightTag/dcjs-in-react). We're still evaluating this technique and are looking forward to community feedback and suggestions on how to make it better.

## The DC Ecosystem

DC is a library that uses D3 to generate SVG charts and Crossfilter.js to manage filtered "views" of data across a large number of dimensions. DC itself is a collection of predefined charts written in D3 together with an integration layer with Crossfilter that creates the interactivity.
 DC provides pre-built charts such as bar charts, heatmaps etc with an API that is flexible enough to allow stacking and customization.

There are other charting libraries that are more beautiful and simpler than DC. What makes DC compelling is that it integrates natively with Crossfilter so that when a user clicks on one chart, all of the others change in response. Crossfilter is optimized to make the requisite data filtering very fast, even on large datasets.

## Why it's hard to integrate DC and React

### Two different paradigms

React feels like a declarative paradigm whereas DC is very much imperative. In React, we declare components and pass options as props, whereas in D3 we modify things until they are ready. Mixing these paradigms can be confusing. If clear borders aren't defined, it can be hard to track where one mode of work ends and the other begins. When thinking about this, our primary concern was maintainability. If using DC introduces so much cognitive overhead that maintaining it becomes hard, it may not be worth it.

### D3 and React both want to control the DOM

React modifies the DOM and D3 does as well. The last thing we'd want is a subtle DOM bug in which it wasn't clear what the source of some change was or a situation where it is hard to predict what is going to happen without knowing React and D3 internals.

### Crossfilter Has It's Own State

You can think of the Crossfilter object as a representation of a state, that combines the original data with the filters applied to it. Crossfilter is built to manage that state and DC is built to interact with Crossfilter's state management. However,  in React, we're often used to having components manage there own state or use an external store like Redux. It's not obvious how to get the two to interact without conflict

### Rerendering Components can lead to bugs

The two issues above may sound vague on their own but should become clearer in the context of re-rendering. If a DC chart is wrapped by a React component and that component is re-rendered, what happens to the chart state and the data state? DC makes no assumptions or guarantees about idempotency (indeed, it's not idempotent) and we are apt to find ourselves with various subtle misbehaviors.
We'd like to be able to reason about three things

1. When will React cause a Chart to rerender
2. Will React ever be able to cause a change in Crossfilter state
3. If the state of Crossfilter changes, will it trigger a render React Components?

## Integrating DC and React

We set out to reimplement the DC.js example in React to see what the answer to those questions could be. In our approach, we hold a Crossfilter object in a Context Provider and render all of the charts as children of that context.

To make the separation of React State and Crossfilter state explicit, we keep the Crossfilter object as a property of the Context Component but external to its state. It's not clear that this is important, but it makes reasoning about Crossfilter's state a little easier.

Each Chart is wrapped in a React component which provides DC with a Ref to a DOM div and access to the Crossfilter object in the context. The component receives a function that passes the ref and Crossfilter object to DC and returns a chart. This approach helps keep the imperative and declarative paradigms separated and makes it easier to reason about the lifecycle of each chart.

### Wrapping Crossfilter in a context provider

Wrapping Crossfilter in context provider is as simple as the code below. The main consideration is that data will probably be loaded asynchronously and that it may take some time for Crossfilter to process it. We don't want to render charts that depend on Crossfilter before we have it, and we don't want to trigger multiple renderings that may reinitialize charts or Crossfilter.

We achieved this by holding Crossfilter as a property of the context component but outside of its state, and maintaining a flag in the context state indicating if we have the Crossfilter object.

```jsx
import * as crossfilter from "crossfilter2";
export class DataContext extends React.Component {
  constructor(props) {
    super(props);
    this.state={loading:false,hasNDX:false};
  }

  componentDidMount(){
      if (this.state.hasNDX){
          return
      }
      if(this.state.loading){
          return
      }
      this.setState({loading:true})

        {/*Do possibly asynchronous things here to get the data and load it into crossfilter */}
        this.ndx = crossfilter(data); //
        this.setState({loading:false,hasNDX:true})
        })
  }

  render() {
      if(!this.state.hasNDX){
          {/*Don't render anything unless we have a crossfilter object */}

          return null;
      }
    return (
      <CXContext.Provider value={{ndx:this.ndx}}>
        <div ref={this.parent}>
        {this.props.children} {/*Render The charts*/}
        </div>
      </CXContext.Provider>
    );
  }
}
```

### A ChartTemplate for DOM Control

As mentioned, we wanted to keep imperative and declarative code separated. We also needed a way to create DOM elements for DC/D3 to attach to, without defining them explicitly.
We settled on a wrapper component that receives as props a **chartFunction**. The chartFunction receives a ref to a dom node and the Crossfilter object and runs DC imperative code on them, returning a DC chart object. The Template Component calls this function inside of an Effect hook and renders the chart.

Using an effect hook ensures that React has already placed the div in the DOM, so we are sure that DC has an element to work on. The useEffect hook has an optional parameter to ensure the effect only runs N times, so we set N to 1 to ensure charts are only created once.

We further wanted to have a Reset button, which could clear any filters applied to a chart. To implement it as a React component we needed to pass it the chart object returned from the **chartFunction**. However, since the chart object was created inside of an effect, it was not immediately accessible during render.

To solve for this, we stored the chart in the component's state using the state hook **setChartOnState**.  This is where restricting the number of calls to the effect hook crucial, as updating state triggers a render and a render calls an effect by default. Without restricting the effect to run only once, this would create an infinite loop.

```jsx
export const ChartTemplate = props => {
    /*
    We render the dc chart using an effect. We want to pass the chart as a prop after the dc call,
    but there is nothing by default to trigger a re-render and the prop, by default would be undefined.
    To solve this, we hold a state key and increment it after the effect ran.
    By passing the key to the parent div, we get a rerender once the chart is defined.
    */
  const context = React.useContext(CXContext);
  const [chart,setChartOnState] = React.useState(null);
  const ndx = context.ndx;
  const div = React.useRef(null);
  React.useEffect(() => {
    const newChart = props.chartFunction(div.current, ndx); // chartfunction takes the ref and does something with it

    newChart.render();
    setChartOnState(newChart);
  },1); {/*Run this exactly once */}
  return (
    <div
      ref={div}
      style={{ width: "100%", minHeight: "100%" }}
      {...props.styles}
    >
     <ResetButton chart={chart} />
    </div>
  );
};
```

### Separating DC Logic and React Logic

With a Chart Template component in place, all that is needed is to write **chartFunctions** for each chart we want to have. Here is an annotated example of what that looks like

```jsx
const dayOfWeekFunc = (divRef, ndx) => {
    const dayOfWeekChart = dc.rowChart(divRef) // Create a rowchart on the Ref
    const dimension = ndx.dimension(function (d) { // Create a crossfilter dimension
        var day = d.dd.getDay();
        var name = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        return day + '.' + name[day];
    });
    const group = dimension.group() // Create a crossfiler group
    dayOfWeekChart
    .dimension(dimension) // Specify the charts dimension
    .group(group) // Specify the charts group

    return dayOfWeekChart // Return the chart object to the template component
}

export const DayOfWeekChart = props => (
    /*
        Call the ChartTemplate Component with the chartFunction
    */
    <ChartTemplate chartFunction={dayOfWeekFunc} />
)
```

Importantly, we're able to completely separate the React code from the DC code which makes reasoning about it and maintaining it easier.

## Benefits, Drawbacks and Next Steps

For us, this was the first step in evaluating the viability of using DC inside of our existing React codebase. The jury is still out, but here is what we know so far

1. It seems we can integrate the two while eliminating the main causes for concern
2. This solution still requires being aware of when components might render and what the implications are.
3. We are able to isolate declarative and imperative code
4. Using DC induces a lot of bespoke code for charts. It's not clear if that is because of DC or because data visualization is bespoke.
5. Styling is still an issue. We need to reconcile between D3 implicit styles, DC styles and the styles we want to use. Our preference is for CSS-in-JS which DC/D3 are not aware of.

If this is relevant to you, please check out the [demo](https://lighttag.github.io/dcjs-in-react/)  [clone the repo](https://github.com/LightTag/dcjs-in-react) and suggest how this can improve.

## References

1. [DC.js Official Site](https://dc-js.github.io/dc.js/)
2. [Crossfilter Official Site](http://square.github.io/crossfilter/)
3. [Crossfilter2](https://github.com/crossfilter/crossfilter) Community Maintained fork of Crossfilter
4. [Easy D3 blackbox components with React hooks](https://swizec.com/blog/easy-d3-blackbox-components-react-hooks/swizec/8689) by Swizec Teller
5. [Effect Hook Documentation](https://reactjs.org/docs/hooks-effect.html)
6. [Our Demo](https://lighttag.github.io/dcjs-in-react/)
7. [GitHub Repo for our code](https://github.com/LightTag/dcjs-in-react)
