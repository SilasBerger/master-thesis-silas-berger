def split_list_into_chunks(target_list, chunk_size):
    num_full_chunks = len(target_list) // chunk_size
    chunks = [target_list[x:(x+chunk_size)] for x in range(0, (num_full_chunks*chunk_size), chunk_size)]
    chunks.append(target_list[(num_full_chunks*chunk_size):-1])
    return chunks