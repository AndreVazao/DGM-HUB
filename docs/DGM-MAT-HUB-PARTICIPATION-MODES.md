# DGM-MAT participation modes in DGM-HUB

The DGM-MAT card exposes three persistent modes as visible controls. They are independent from the start/stop controls used by other providers.

## Modes

- **Off**: DGM-MAT is removed from Hub chat targets and the Hub requests the passive observer to stop. The central DGM-MAT runtime is deliberately left running.
- **Observer**: DGM-MAT can be selected as a Hub chat target and records the user request in the Hub event journal, but it does not produce a conversational answer. The current installed DGM-MAT runtime does not expose the passive observer start/stop API, so this mode does not monitor other providers in the background. The UI states this limitation.
- **Respond**: the Hub disables passive observation and sends the user's message to the authenticated DGM-MAT local conversation API. The thread ID is persisted per Hub conversation. Selecting this mode automatically selects DGM-MAT alone and clears other provider selections; the user can add other providers afterwards.

The **Só DGM-MAT** action switches to Respond and clears all other provider selections. The normal provider checkboxes remain available for explicit multi-agent requests.

## Safety

- Changing mode never terminates the DGM-MAT runtime.
- Off is persisted as mode=off and enabled=false.
- A failed observer-control request does not persist a new mode.
- DGM-MAT chat is rejected by the Hub while mode Off has disabled the provider.
- DGM-MAT responses still pass through its authenticated local API and existing mission/approval governance.
- The passive observer API must be deployed in DGM-MAT before Observer can monitor conversations from other providers without being selected in the Hub.

## Validation

The DGM-MAT responder tests cover authenticated responses, persistent thread mapping, observer/respond/hybrid dispatch, mode transitions, off-mode rejection, and the visible three-mode UI.
