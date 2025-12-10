"""
Class: CS230--Section 1
Name: Ryan Bauer
Description: Final Project
I pledge that I have completed the programming assignment
independently.
I have not copied the code from a student or any source.
I have not given my code to any student
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pydeck as pdk
from collections import Counter


#loads the data from the CSV file
def loadData():

    df = pd.read_csv("Files/Meteorite_Landings.csv")

    #Cleans the data headers so don't get probems 
    df.columns = [col.lower().replace(" ","_").replace("(","").replace(")","") for col in df.columns]

    #remove incomplete rows
    df = df.dropna(subset=["reclat","reclong","mass_g","year"])

    #make year a numnber
    df["year"] = df["year"].astype(int)

    return df

#Calculates the kinetic energy of a meteorite returns energy in joules and a classification
def calculateThreat(massGrams, velocity_kms=15):
    #convert units to those needed for cal
    massKg = massGrams / 1000
    velocity_ms = velocity_kms * 1000

    energyJoules = .5 * massKg * (velocity_ms ** 2)

    #lable levels 
    if energyJoules > 1e12:
        intensity = "Catastrophic"
    elif energyJoules > 1e9:
        intensity = "Severe"
    elif energyJoules > 1e6:
        intensity = "Moderate"
    else:
        intensity = "Minimal"

    return energyJoules , intensity

#Returns the descritption of the class names
def getClassDescription(className):
    descriptions = {
        "L6": "Low Iron Chondrite (Type 6). The most common type. 'L' means low iron content, and '6' means it was heated severely inside its parent asteroid, altering its original structure.",
        "H5": "High Iron Chondrite (Type 5). 'H' stands for High iron content. Type 5 means it experienced significant heating (metamorphism), but less than Type 6.",
        "L5": "Low Iron Chondrite (Type 5). Similar to L6 but slightly less altered by heat. It contains distinct chondrules (mineral grains) that are starting to blur together.",
        "H6": "High Iron Chondrite (Type 6). High metal content and very strongly heated. The internal structure is recrystallized, making chondrules hard to see.",
        "H4": "High Iron Chondrite (Type 4). 'H' type with only moderate heating. The original mineral grains (chondrules) are still very distinct and easy to see.",
        "LL5": "Low-Low Chondrite (Type 5). 'LL' means Low Iron and Low Metal. These are rare ordinary chondrites that contain very little free metal.",
        "LL6": "Low-Low Chondrite (Type 6). An LL type that has been strongly heated, merging its minerals together.",
        "L4": "Low Iron Chondrite (Type 4). An L type that is relatively pristine. It hasn't been melted or altered as much as L5 or L6.",
        "CM2": "Carbonaceous Chondrite. Very rare and primitive! These contain water, carbon, and organic compounds from the early solar system.",
        "Iron": "Iron Meteorite. Composed almost entirely of nickel-iron metal. These are likely the cores of dead asteroids that were destroyed."
    }
    return descriptions.get(className, "A specific classification of meteorite based on its chemical composition and texture.")

#main func that has creates the website
def main():
    st.set_page_config(page_title="Celestial Impacts", layout="wide")

    #Code for the floating header
    header_html = """
    <style>
        /* main container */
        .fixed-header-container {
            position: fixed;
            top: 40px;           
            left: 0;
            width: 100%;         
            background-color: #FFFFF7;
            z-index: 9999;
            border-bottom: 1px solid #dcdcdc;
        }
    
        /* so can be alined */
        .fixed-header-content {
            max-width: 60rem; 
            margin: 0 auto;      
            padding: 1rem 1rem;  
            text-align: center;    
        }
        
        /* make so does not overlap others */
        .block-container {
            padding-top: 110px; 
        }
    </style>

    <div class="fixed-header-container">
        <div class="fixed-header-content">
            <h1 style="margin: 0; padding: 0;">🚀Celestial Impacts: The Meteorite Tracker</h1>
        </div>
    </div>
    """

    #write the HTML code 
    st.markdown(header_html, unsafe_allow_html=True)

    #Load the data in
    data = loadData()

    #set up the pages 
    st.sidebar.title("Pages")
    page = st.sidebar.radio("Go to", ["Dashboard", "Meteorite Encyclopedia"])
    st.sidebar.divider()

    # page 1 main page
    if page == "Dashboard":

        st.subheader("Explore the history of meteorite landings on Earth.")

        # set up the filters 
        st.sidebar.header("Filter Options")

        #Year Filter
        minYear = int(data['year'].min())
        maxYear = int(data['year'].max()) #Can't use this because one data point that is in the future
        yearRange = st.sidebar.slider(
            "Select Year Range",
            min_value=minYear,
            max_value=2025,
            value=(1900, 2025)
        )

        #Weight Filter
        minWeight = int(data['mass_g'].min())
        maxWeight = int(data['mass_g'].max()) 
        weightRange = st.sidebar.slider(
            "Select Range of Weight in Grams",
            min_value= minWeight,
            max_value= maxWeight,
            value=(1, maxWeight)
        )

        #fall Filter
        FallFoundOptions = ["Fell","Found"]
        selectedFallFound = st.sidebar.multiselect(
            "Select Fallen or Found (Leave empty for all)",
            FallFoundOptions,  # show top 10 as default
            default=[]
        )

        #Class Filter
        classesCounts = Counter(data["recclass"])
        top10Tuple = classesCounts.most_common(10)
        top10 = list(zip(*top10Tuple))
        selectedClasses = st.sidebar.multiselect(
            "Select Meteorite Class (Leave empty for all)",
            top10[0],  # show top 10 as default
            default=[]
        )


        #Data Filtering the DF
        #Year, Mass, and make sure valid and has a mass
        filteredDF = data[(data["year"] >= yearRange[0]) & (data["year"] <= yearRange[1]) &
                          (data["mass_g"] >= weightRange[0]) & (data["mass_g"] <= weightRange[1])&
                          (data["nametype"] == "Valid") &
                          (data["mass_g"] > 0)]


        #If it fell
        if selectedFallFound:
            filteredDF = filteredDF[filteredDF["fall"].isin(selectedFallFound)]
        #What the class is 
        if selectedClasses:
            filteredDF = filteredDF[filteredDF["recclass"].isin(selectedClasses)]

        #Sort the DF
        filteredDF = filteredDF.sort_values(by="mass_g", ascending=False)
        
        #Create the map
        st.subheader(f"Global Impact Map ({len(filteredDF)} Meteorites)")

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filteredDF,
            get_position=["reclong","reclat"],
            get_color=[200,30,0,160],
            get_radius="mass_g",
            radius_scale=0.05,
            radius_min_pixels=3,
            radius_max_pixels=50,
            pickable=True
        )
        viewState = pdk.ViewState(
            latitude=20,
            longitude=0,
            zoom=1,
            pitch=0
        )
        st.pydeck_chart(pdk.Deck(
            map_provider="carto",
            map_style=pdk.map_styles.CARTO_ROAD,
            initial_view_state=viewState,
            layers=[layer],
            tooltip={"text": "{name}\nMass: {mass_g}g\nYear: {year}\n{fall}\nClass: {recclass}\n"} #tooltips
        ))
        st.divider()


        #Set up the lookup
        st.subheader("Meteorite Lookup")
        #Create a list of names from filtered data
        # sort them so it is easier to find specific ones
        meteorite_names = sorted(filteredDF["name"].unique())
        #Create the search box
        # index=None makes it start empty so the user sees the placeholder
        selected_name = st.selectbox(
            "Search for a meteorite by name:",
            options=meteorite_names,
            index=None,
            placeholder="Type to search:"
        )
        #Display the link when a user selects a name
        if selected_name:
            row = filteredDF[filteredDF["name"] == selected_name].iloc[0]
            #Create the link
            link = f"https://www.lpi.usra.edu/meteor/metbull.php?code={row['id']}"
            # Show the details and the button next to each other
            colSearch1, colSearch2 = st.columns([3, 1])
            with colSearch1:
                st.info(f"**Selected:** {row['name']} | **Mass:** {row['mass_g']}g | **Class:** {row['recclass']}")
            with colSearch2:
                st.link_button("View Official Report", link)

        #Make sure that there is data in the data set
        if(len(filteredDF)) > 0:

            #Set up split screen 
            col1, col2 = st.columns(2)



            #on the left
            with col1:
                #give 2 options for chart type
                chartOption = st.radio("Chose Chart Style:", ["2 Seprate Bar Graphs", "Log Scale Line Chart"], horizontal=True)

                #Log Scale
                if chartOption == "Log Scale Line Chart":
                    st.subheader("Discovery Timeline: Fell vs. Found")
                    #Set up the pivot table
                    pivotData = filteredDF.pivot_table(
                        index="year",
                        columns="fall",
                        values="id",
                        aggfunc="count",
                        fill_value=0
                    ) + 1 #so 0's don't mess up the log scale

                    fig, ax = plt.subplots()
                    #print the chart
                    pivotData.plot(ax=ax)
                    ax.set_yscale("log")
                    ax.set_ylabel("Count (Log Scale)")
                    ax.legend(title=None)
                    st.pyplot(fig)
                    st.caption("Compare observed falls (rare) vs. random finds (common)")
                
                #2 bar Charts
                else:
                    st.subheader("Discovery Timeline: Fell vs. Found")

                    # Set up the pivot table
                    pivotData = filteredDF.pivot_table(
                        index="year",
                        columns="fall",
                        values="id",
                        aggfunc="count",
                        fill_value=0
                    )

                    #Chart of Falls
                    st.caption("Observed Falls (Rare)")
                    fig1, ax1 = plt.subplots()
                        
                        # Check if data exists to avoid errors
                    if 'Fell' in pivotData.columns:
                        ax1.bar(pivotData.index, pivotData['Fell'], color='skyblue')
                        ax1.set_ylabel("Count")
                        ax1.set_xlabel("Year")
                        st.pyplot(fig1)

                    #Chart of Finds
                    st.caption("Random Finds (Common)")
                    fig2, ax2 = plt.subplots()
                    if 'Found' in pivotData.columns:
                        ax2.bar(pivotData.index, pivotData['Found'], color='orange')        
                        ax2.set_ylabel("Count")
                        ax2.set_xlabel("Year")
                        st.pyplot(fig2)


            #on the Right
            with col2:
                #Set up pie chart
                st.subheader("Composition Analysis")
                classCounts = filteredDF["recclass"].value_counts().to_dict()
                #Find top 5 classes
                top5 = dict(list(classCounts.items())[:5])
                othersCount = sum(list(classCounts.values())[5:])
                top5["Others"] = othersCount
                #Print pie chart
                fig, ax = plt.subplots()
                ax.pie(top5.values(),labels=top5.keys(),autopct="%1.1f%%")
                st.pyplot(fig)
            st.divider()


            #Threat Analysus
            st.subheader("Threat Analysis")
            maxMass = filteredDF["mass_g"].max()
            maxMeteor = filteredDF[filteredDF["mass_g"] == maxMass].iloc[0]
            st.write(f"The heaviest meteorite in this section is **{maxMeteor['name']}**({maxMass:,.0f} g).")
            st.write("Kinetic Energy of Top 3 Heaviest:")
            top3 = filteredDF.head(3)
            #print out the top 3 and traits
            for index, row in top3.iterrows():
                energy, label = calculateThreat(row["mass_g"])
                st.write(f"- **{row['name']}**: {energy:,.0f} Joules ({label})")


    #Next page
    elif page == "Meteorite Encyclopedia":
        st.title("📚 Meteorite Encyclopedia")
        #set up left and right with left being des. and right being the image
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("What is a Meteorite")
            st.write("Meteoroids are space rocks that range in size from dust grains to small asteroids. This term only "
                     "applies when these rocks while they are still in space.Most meteoroids are pieces of other, larger "
                     "bodies that have been broken or blasted off. Some come from comets, others from asteroids, and some "
                     "even come from the Moon and other planets. Some meteoroids are rocky, while others are metallic, or "
                     "combinations of rock and metal. When meteoroids enter Earth’s atmosphere, or that of another planet,"
                     " at high speed and burn up, they’re called meteors. This is also when we refer to them as “shooting "
                     "stars.” Sometimes meteors can even appear brighter than Venus – that’s when we call them “fireballs.” "
                     "Scientists estimate that about 48.5 tons (44,000 kilograms) of meteoritic material falls on Earth "
                     "each day.(NASA)")
        with col2:
            st.image("Files/sky.jpg")
            #st.image("Files/ground.jpg")
        st.divider()

        #Explain the most common type of rock types
        st.title("Most common types of space rocks found:")
        st.info("The classification code (e.g., L6, H5) tells us the chemical composition and how much the rock was heated.")

        #get the most common rock classes
        top10Types = data['recclass'].value_counts().head(10)
        #print out the data
        for type_name, count in top10Types.items():
            description = getClassDescription(type_name)
            with st.container():
                st.subheader(f"{type_name} (Count: {count})")
                st.write(description)
                st.divider()

                
#Run everthing 
if __name__ == "__main__":
    main()
