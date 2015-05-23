import networkx as nx
import pandas as pd

def labeled_blockmodel(g,partition):
    """
    Perform blockmodel transformation on graph *g*
    and partition represented by dictionary *partition*.
    Values of *partition* are used to partition the graph.
    Keys of *partition* are used to label the nodes of the
    new graph.
    """
    new_g = nx.blockmodel(g,partition.values())
    labels = dict(enumerate(partition.keys()))
    new_g = nx.relabel_nodes(new_g,labels)
    
    return new_g

def repartition_dataframe(df,partition):
    """
    Create a new dataframe with the same index as
    argument dataframe *df*, where columns are
    the keys of dictionary *partition*.
    The data of the returned dataframe are the
    combinations of columns listed in the keys of
    *partition*
    """
    df2 = pd.DataFrame(index=df.index)

    for k,v in partition.items():
        df2[k] = df[v[0]]
    
        for i in range(len(v) - 1):
            df2[k] = df2[k] + df[v[i]]

    return df2

def get_common_head(str1,str2,delimiter=None):
    try:
        if str1 is None or str2 is None:
            return '', 0
        else:
            #this is ugly control flow clean it
            if delimiter is not None:

                dstr1 = str1.split(delimiter)
                dstr2 = str2.split(delimiter)

                for i in range(len(dstr1)):
                    if dstr1[:i] != dstr2[:i]:
                        #print list1[:i], list2[:i]
                        return delimiter.join(dstr1[:i-1]),i-1
                return str1,i
            else:
                for i in range(len(str1)):
                    if str1[:i] != str2[:i]:
                        #print list1[:i], list2[:i]
                        return str1[:i-1],i-1
                return str1[:i],i

        return '', 0
    except Exception as e:
        print e
        return '', 0

def get_common_foot(str1,str2,delimiter=None):
    head, ln = get_common_head(str1[::-1],str2[::-1],delimiter=delimiter)

    return head[::-1],ln

# turn these into automated tests
#print get_common_head('abcdefghijklmnop','abcde12345')
#print get_common_head('abcdefghijklmnop',None)
#print get_common_head('abcde\nfghijk\nlmnop\nqrst','abcde\nfghijk\nlmnopqr\nst',delimiter='\n')

def remove_quoted(mess):
    message = [line for line in mess.split('\n')
               if len(line)!=0 and line[0] != '>' and line[-6:] != 'wrote:']
    new = '\n'.join(message)
    return new

## remove this when clean_message is added to generic libraries
def clean_message(mess):
    if mess is None:
        mess = ''
    
    mess = remove_quoted(mess)

    mess = mess.strip()

    return mess

