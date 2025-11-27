## Game Content Generation Pipeline for Intergenerational Stories

This project is the official code implementation of the paper "Enhancing Young People's Understanding of Intergenerational Stories through Generative Games: A Case Study on Conveying Experiences and Perspectives". This pipeline can automatically convert structured story texts based on **Labov's narrative framework** into two core game content files: **Interactive Narrative Game** and **AI Role-Playing Game**.

We provide a story case `StoryExample.txt` to demonstrate the complete end-to-end process.

### Pipeline Overview

The main entry script `story_to_game_pipeline.py` orchestrates the entire process:

```
[StoryExample.txt] -> story_to_game_pipeline.py
                          |
                          +---> interactive_story_game_pipeline.py -> [interactive_story_game.json]
                          |
                          +---> role_playing_game_pipeline.py ------> [role_playing_game.json]
```

### Prompts

All core prompts are defined in `system_prompt.py`. They are crucial for implementing the transformation from narrative to game logic.

#### 1. Interactive Narrative Generation
This process is driven by `interactive_story_game_pipeline.py` and primarily includes the following prompts:

-   **`story_to_dmc`**:
    -   **Corresponding to paper**: Section 5.2.2, Step 1 (Identify decisions and core constraints).
    -   **Function**: Analyzes the "Complicating Action" section of the story and extracts the protagonist's structured decision-making and causality chain (Decision-Making and Causality, DMC). This is the foundational data for constructing branching narratives.

-   **`dmc_to_branch`**:
    -   **Corresponding to paper**: Section 5.2.2, Step 2 & 3 (Generate counterfactual options & Construct "failure" narratives).
    -   **Function**: Based on the DMC chain, generates "counterfactual" distractor options for each decision point and designs logically coherent "failure" or explanatory narratives for these non-mainline choices.

#### 2. AI Role-Playing Game Generation
This process is driven by `role_playing_game_pipeline.py` and implemented through a series of chained prompts:

-   **`pd_recognition`**:
    -   **Corresponding to paper**: Section 5.3.
    -   **Function**: As the **first step** of RPG generation, precisely identifies and extracts **Perspective Discussion (PD)** that carries core viewpoints from the "Coda" section of the story.

-   **`extract_key_points`**:
    -   **Corresponding to paper**: Section 5.3.
    -   **Function**: Combines the extracted PD with the complete story to distill several **core perspectives** suitable for debate. These perspectives serve as the foundation for AI character configuration.

-   **`role_play_game_generation`**:
    -   **Corresponding to paper**: Section 5.3.
    -   **Function**: Selects a core perspective and generates a complete AI character configuration holding an **opposing stance**, including background story, personality, dialogue objectives, and initial debate scenario.

#### 3. Asset Generation
These prompts are used to generate visual elements that enhance game immersion:

-   **`define_narrative_standards` & `drawIllustration`**: Generate stylistically consistent illustrations for each scene in the interactive narrative game.
-   **`role_play_external_message`**: Generate visual information such as character portraits and identity-appropriate scenes for the AI role-playing game.

### **Usage**

1.  **Implement API Functions**: 
    First, you need to implement your own LLM and image generation logic in `chat.py`:
    - **`generate_text()`**: Implement your preferred LLM API call (cloud-based like OpenAI, Anthropic, or local deployment like Ollama)
    - **`generate_image()`**: Implement your preferred image generation API call (like Stability AI, DALL-E, or local models like Stable Diffusion)

2.  **Execute Pipeline**:
    Once the API functions are implemented, run the main pipeline:
    ```bash
    python story_to_game_pipeline.py
    ```
    The script will read `StoryExample.txt`, process it, and generate corresponding game directories with JSON files and assets in the `output/` directory, which can be directly loaded into compatible game software.

### **Game Visualization Tool**

We provide a Unity-based game viewer for loading and displaying the generated game content files, facilitating validation of generation results within a graphical environment.

- **Download**: You can download the tool from: `https://drive.google.com/file/d/1aKqrJh5PgpCA7mAai_IoDBus4Kk2sI8N/view?usp=sharing`
- **Usage**: Simply extract the archive, launch `game-visualization-tool.exe`, and enter the path to your game files (the `output/` directory).
- **Note**: For ready-made game files for testing, please contact the author.