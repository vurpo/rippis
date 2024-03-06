<script lang="ts">
    type Track = {TRACKNUM?: string, TITLE: string, ALBUM?: string, ARTIST: string}
    export let meta: Map<string, Track>;

    function tracks(): Track[] {
        return Array.from(meta.keys())
            .filter((k) => k !== "album")
            .sort((a, b) => Number(a) - Number(b))
            .map((k) => <Track>meta.get(k))
    }
</script>

<div>
    <table>
        {#each tracks() as track}
        <tr><td>{track.TRACKNUM}</td><td>{track.TITLE}</td><td>{track.ALBUM}</td><td>{track.ARTIST}</td></tr>
        {/each}
    </table>
</div>

<style>
    table {
        border-collapse: collapse;
    }
    td {
        padding: 0.2em;
        border: 1px solid black;
        font-size: 0.9rem;
    }
</style>