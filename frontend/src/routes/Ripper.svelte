<script lang="ts">
	import { onMount, tick } from "svelte";
	import MetadataTable from "./MetadataTable.svelte";
	import { select_option } from "svelte/internal";

    export let endpoint: string;
    export let name: string;

    let connected = false;

    let ripper_state = new Set<string>();
    let ripper_log = "";
    let rip_state_string = "Reading TOC"
    let textarea: HTMLTextAreaElement;
    let meta_alternatives: any[] = [];

    let selected_metadata: any = undefined;
    let selected_tracks: any[] = [];
    let selected_album_name: string | undefined = undefined;
    let edit_metadata = false;

    $: if (selected_metadata){
        selected_tracks = Object.keys(selected_metadata)
            .filter((k) => k !== "album")
            .sort((a, b) => Number(a) - Number(b))
            .map((k) => selected_metadata[k])
    }

    $: if (selected_album_name) {
        for (const track of selected_tracks) {
            track.ALBUM = selected_album_name
        }
    }

    let socket: WebSocket;

    async function send_selected_tracks() {
        const finished = selected_tracks.reduce((a, v) => ({ ...a, [v.TRACKNUM]: v}), {})
        console.log(finished)
        socket.send(JSON.stringify({"metadata":finished}))
    }

    onMount(async () => {
        await connect()
    })


    async function connect() {
        console.log(`connecting to ${endpoint}`)
		socket = new WebSocket(endpoint)

        const timeout = setTimeout(() => {
            socket.close()
        }, 2000)

        socket.onopen = () => {
            clearTimeout(timeout)
            connected = true
        }

        socket.onerror = (e) => {
            clearTimeout(timeout)
            console.log("websocket error", e)
            connected = false
        }

        socket.onclose = () => {
            clearTimeout(timeout)
            console.log("websocket close")
            connected = false
            setTimeout(connect, 500)
        }

        //...and so on

        socket.onmessage = async (event) => {
            let { state, set_state, remove_state, rip_log, rip_log_line, alternatives} = JSON.parse(event.data)

            if (state) {
                ripper_state.clear()
                for (const s of state) {
                    ripper_state.add(s)
                }
                ripper_state = ripper_state
            }

            if (set_state) {
                ripper_state.add(set_state)
                ripper_state = ripper_state
            }

            if (remove_state) {
                ripper_state.delete(remove_state)
                ripper_state = ripper_state
            }

            if (rip_log) {
                ripper_log = rip_log
                await tick()
                textarea.scrollTop = textarea.scrollHeight
                const matches = [...rip_log.matchAll(/Reading track [0-9]+ of [0-9]+/g)]
                if (matches.length > 0) {
                    rip_state_string = matches[matches.length - 1][0]
                }
                if (rip_log.match(/Getting length of audio track/)) {
                    rip_state_string = "Finishing"
                }
                
            }

            if (rip_log_line) {
                ripper_log += rip_log_line
                await tick()
                textarea.scrollTop = textarea.scrollHeight
                const match = rip_log_line.match(/Reading track [0-9]+ of [0-9]+/)
                if (match) {
                    rip_state_string = match[0]
                }
                if (rip_log_line.match(/Getting length of audio track/)) {
                    rip_state_string = "Finishing"
                }
            }

            if (alternatives) {
                meta_alternatives = alternatives
            } 
        }
	}
</script>

<div class="ripper">
    {#if connected}
        {#if ripper_state.has("waiting_for_disc")}
            <div class="big-state"><img class="big-icon" src="/cd.svg" alt="ripping" />Insert a disc into drive {name}</div>
        {:else if ripper_state.has("getting_metadata")}
            <div class="big-state"><img class="big-icon rotate" src="/cd.svg" alt="ripping" />Looking up disc metadata...</div>
        {:else}
            {#if ripper_state.has("ripping_disc")}
                <div class="box ripping-status"><img class="ripping-icon rotate" src="/cd.svg" alt="ripping" /> Ripping CD... ({rip_state_string})</div>
            {:else if ripper_state.has("finished_ripping")}
                <div class="box ripping-status"><img class="ripping-icon" src="/cd.svg" alt="ripping" /> Finished ripping.</div>
            {/if}
            <details class="box">
                <summary>Detailed ripping information</summary>
                <textarea readonly bind:this={textarea} bind:value={ripper_log} rows="23" cols="80"/>
            </details>
            <h1>Album metadata</h1>
            {#if ripper_state.has("waiting_for_metadata")}
                {#if selected_metadata === undefined}
                    <div class="box">Confirm one of the following metadata alternatives, or edit before confirming.</div>
                    {#each meta_alternatives as meta}
                        <div class="meta-row">
                            <MetadataTable meta={new Map(Object.entries(meta))} />
                            <div class="meta-buttons">
                                <button on:click={async () => {selected_metadata = meta; await tick(); send_selected_tracks()}}>Confirm</button>
                                <button on:click={() => {selected_metadata = meta; selected_album_name = meta.album.TITLE; edit_metadata = true;}}>Edit</button>
                            </div>
                        </div>
                    {/each}
                {:else if edit_metadata}
                <div class="box">Edit the album metadata before confirming.</div>
                <div class="meta-row">
                    <table>
                        {#each selected_tracks as track}
                            <tr>
                                <td>{track.TRACKNUM}</td>
                                <td class="edit" contenteditable="true" bind:innerHTML={track.TITLE} />
                                <td class="edit" contenteditable="true" bind:innerHTML={selected_album_name} />
                                <td class="edit" contenteditable="true" bind:innerHTML={track.ARTIST} />
                            </tr>
                        {/each}
                    </table>
                    <button on:click={() => {send_selected_tracks(); edit_metadata = false;}}>Confirm</button>
                </div>
                {:else}
                <div class="box ripping-status"><img class="ripping-icon rotate" src="/cd.svg" alt="ripping" /> Metadata confirmed...</div>
                <table>
                    {#each selected_tracks as track}
                        <tr>
                            <td>{track.TRACKNUM}</td>
                            <td>{track.TITLE}</td>
                            <td>{selected_album_name}</td>
                            <td>{track.ARTIST}</td>
                        </tr>
                    {/each}
                </table>
                {/if}
            {:else if ripper_state.has("received_metadata")}
                <div class="box ripping-status">Metadata confirmed.</div>
                <table>
                    {#each selected_tracks as track}
                        <tr>
                            <td>{track.TRACKNUM}</td>
                            <td>{track.TITLE}</td>
                            <td>{selected_album_name}</td>
                            <td>{track.ARTIST}</td>
                        </tr>
                    {/each}
                </table>
            {/if}
        {/if}
    {:else}
        <div class="big-state"><img class="big-icon rotate" src="/cd.svg" alt="ripping" />Initializing, please wait...</div>
    {/if}
</div>

<style>
    @keyframes rotation {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(359deg);
        }
    }

    table {
        border-collapse: collapse;
    }
    td {
        padding: 0.2em;
        border: 1px solid black;
        font-size: 0.9rem;
    }

    .edit {
        background-color: white;
    }

    .ripper {
        padding: 0.7em;
    }

    .box {
        margin-bottom: 0.5em;
    }

    .big-state {
        margin: 2em auto 0 auto;
        width: fit-content;
        font-size: 1.5rem;
        display: flex;
        flex-direction: row;
        gap: 0.5em;
        align-items: center;
    }

    .big-icon {
        width: 1.5em;
        height: 1.5em;
    }

    .meta-row {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 1em;
        margin-bottom: 0.5em;
    }

    .meta-buttons {
        display: flex;
        flex-direction: column;
    }

    .ripping-status {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 0.2em;
    }

    .ripping-icon {
        height: 1.2em;
        width: 1.2em;
    }

    .rotate {
        animation: rotation 1s infinite linear;
    }
</style>
